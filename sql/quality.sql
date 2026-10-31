-- name: overview
with per_user as (
    select user_id, count(*) as n_exp
    from exp_students
    group by user_id
)
select
    (select count(*) from exp_students) as n_rows,
    (select count(distinct experiment_id) from exp_students) as n_experiments,
    count(*) as n_users,
    count(*) filter (where n_exp > 1) as n_users_multi,
    avg((n_exp > 1)::int) as share_users_multi,
    (select sum(problem_count) from exp_students) as n_problems
from per_user;

-- name: per_experiment
select
    exp_no,
    experiment_id,
    any_value(experiment_name) as experiment_name,
    count(*) as n_rows,
    count(distinct user_id) as n_users,
    sum(problem_count) as n_problems,
    count(*) filter (where grp = 'C') as n_c,
    count(*) filter (where grp = 'E') as n_e
from exp_students
group by all
order by exp_no;

-- name: xlsx_diff
-- Сверка значений CSV и xlsx в длинном формате. Ячейки равны, если совпадают как текст (пустая строка = NULL),
-- как числа с точностью 1e-6 (в xlsx log(count) записан с полной точностью) или как булевы (TRUE и 1).
-- NULL заменяю пустой строкой до разворота, иначе unpivot их выбрасывает.
with c as (
    unpivot (
        select problem_set, "User ID", coalesce(columns(* exclude (problem_set, "User ID")), '')
        from read_csv(getvariable('csv_path'), header = true, all_varchar = true)
    )
    on columns(* exclude (problem_set, "User ID")) into name col value v
),
x as (
    unpivot (
        select problem_set, "User ID", coalesce(columns(* exclude (problem_set, "User ID")), '')
        from (
            select * rename (Condition as InferredCondition)
            from read_xlsx(getvariable('xlsx_path'), all_varchar = true)
        )
    )
    on columns(* exclude (problem_set, "User ID")) into name col value v
)
select
    coalesce(c.col, x.col) as col,
    count(*) filter (where x.col is null) as only_csv,
    count(*) filter (where c.col is null) as only_xlsx,
    count(*) filter (where c.col is not null and x.col is not null and not (
        c.v = x.v
        or abs(try_cast(c.v as double) - try_cast(x.v as double)) < 1e-6
        or try_cast(c.v as boolean) = try_cast(x.v as boolean)
    )) as n_diff
from c
full join x on c.problem_set = x.problem_set and c."User ID" = x."User ID" and c.col = x.col
group by all
order by n_diff desc, col;

-- name: duplicates
-- Строки, совпадающие во всём, кроме user_id, - не дубли, если у учеников нет истории:
-- тогда все ковариаты пустые и строки различаются только исходом.
with near as (
    select * exclude (user_id), count(*) as k
    from exp_students
    group by all
    having count(*) > 1
)
select
    (select count(*) from raw) - (select count(*) from (select distinct * from raw)) as full_duplicates,
    (select count(*) from (
        select experiment_id, user_id from exp_students group by all having count(*) > 1
    )) as user_twice_in_experiment,
    (select count(*) from (
        select user_id from exp_students group by user_id having count(distinct grp) > 1
    )) as users_in_both_groups_across_experiments,
    count(*) as same_but_user_groups,
    coalesce(sum(k), 0) as same_but_user_rows,
    count(*) filter (where prior_problem_count is null) as same_but_user_groups_without_history
from near;

-- name: invalid_values
unpivot (
    select
        count(*) filter (where grp not in ('C', 'E')) as grp_not_c_e,
        count(*) filter (where complete not in (0, 1)) as complete_not_binary,
        count(*) filter (where could_see_video not in (0, 1)) as video_not_binary,
        count(*) filter (where problem_count < 0) as problem_count_negative,
        count(*) filter (where prior_pct_correct not between 0 and 1
            or prior_pct_completion not between 0 and 1
            or prior_class_pct_completion not between 0 and 1
            or prior_hw_pct_completion not between 0 and 1
            or prior_class_hw_pct_completion not between 0 and 1) as share_out_of_0_1,
        count(*) filter (where prior_correct_count > prior_problem_count) as correct_gt_problems,
        count(*) filter (where prior_completion_count > prior_assignment_count) as completed_gt_started,
        count(*) filter (where prior_assignment_count > prior_assignments_assigned) as started_gt_assigned,
        count(*) filter (where prior_hw_completion_count > prior_hw_count) as hw_completed_gt_started,
        count(*) filter (where prior_hw_count > prior_hw_assigned) as hw_started_gt_assigned,
        count(*) filter (where abs(prior_pct_correct - prior_correct_count / prior_problem_count) > 1e-6)
            as pct_correct_mismatch,
        count(*) filter (where abs(prior_pct_completion - prior_completion_count / prior_assignment_count) > 1e-6)
            as pct_completion_mismatch,
        count(*) filter (where abs(prior_hw_pct_completion - prior_hw_completion_count / prior_hw_count) > 1e-6)
            as hw_pct_completion_mismatch,
        count(*) filter (where complete = 1 and abs(log_count - log10(problem_count)) > 1e-6) as log_mismatch,
        count(*) filter (where complete = 1 and log_count is null) as log_missing_for_complete,
        count(*) filter (where complete = 0 and log_count is not null) as log_for_incomplete,
        -- в анализе не используются, только для отчёта
        count(*) filter (where birthyear is null) as birthyear_missing,
        count(*) filter (where birthyear not between 1990 and 2008) as birthyear_implausible,
        count(*) filter (where class_grade is null) as class_grade_missing,
        count(*) filter (where not regexp_full_match(class_grade, '\d+')) as class_grade_as_word,
        count(*) filter (where gender = 'Unknown') as gender_unknown
    from exp_students
) on columns(*) into name check_name value n_rows;

-- name: experienced_by_group
select
    exp_no,
    experiment_id,
    count(*) filter (where grp = 'C') as n_c,
    count(*) filter (where grp = 'E') as n_e,
    count(*) filter (where not experienced and grp = 'C') as not_exp_c,
    count(*) filter (where not experienced and grp = 'E') as not_exp_e,
    avg((not experienced)::int) filter (where grp = 'C') as share_not_exp_c,
    avg((not experienced)::int) filter (where grp = 'E') as share_not_exp_e
from exp_students
group by all
order by exp_no;

-- name: experienced_outcomes
-- Кто не увидел условие: бросил раньше или решил без ошибок.
select
    exp_no,
    experienced,
    count(*) as n,
    avg(complete) as completion,
    median(problem_count) as median_problems,
    avg((complete = 1 and problem_count <= 3)::int) as share_done_in_3,
    avg((complete = 0 and problem_count <= 2)::int) as share_quit_by_2
from exp_students
where experiment_id in (select experiment_id from exp_students where not experienced)
group by all
order by exp_no, experienced;

-- name: video_check
select
    exp_no,
    experiment_id,
    grp,
    count(*) as n,
    count(could_see_video) as n_checked,
    count(*) filter (where could_see_video = 0) as n_cannot_see,
    avg(1 - could_see_video) as share_cannot_see
from exp_students
where experiment_id in (select experiment_id from exp_students where could_see_video is not null)
group by all
order by exp_no, grp;

-- name: completion_rule
-- Минимум задач у завершивших. При правиле «три подряд» он не может быть меньше 3.
select
    exp_no,
    experiment_id,
    count(could_see_video) > 0 as has_video_check,
    count(*) filter (where complete = 1) as n_done,
    min(problem_count) filter (where complete = 1) as min_done,
    min(problem_count) filter (where complete = 1 and grp = 'C') as min_done_c,
    min(problem_count) filter (where complete = 1 and grp = 'E') as min_done_e,
    count(*) filter (where complete = 1 and problem_count = 2) as n_done_2,
    count(*) filter (where complete = 1 and problem_count = 3) as n_done_3,
    count(*) filter (where complete = 1 and problem_count = 2 and grp = 'C') as n_done_2_c,
    count(*) filter (where complete = 1 and problem_count = 2 and grp = 'E') as n_done_2_e
from exp_students
group by all
order by exp_no;

-- name: done_in_2_by_video
-- Завершившие в экспериментах, где встречается завершение за 2 задачи, по итогу проверки видео.
select
    could_see_video,
    count(*) as n_done,
    count(*) filter (where problem_count = 2) as n_done_2,
    count(*) filter (where problem_count = 3) as n_done_3,
    avg((problem_count = 2)::int) as share_done_2
from exp_students
where complete = 1
  and experiment_id in (select experiment_id from exp_students where complete = 1 and problem_count = 2)
group by all
order by all;

-- name: done_distribution_by_video
select could_see_video, least(problem_count, 10) as problem_count, count(*) as n
from exp_students
where complete = 1
  and experiment_id in (select experiment_id from exp_students where complete = 1 and problem_count = 2)
group by all
order by all;

-- name: zero_problems
select exp_no, experiment_id, complete, experienced, count(*) as n
from exp_students
where problem_count = 0
group by all
order by all;
