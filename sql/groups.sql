-- name: group_sizes
-- Размеры групп для SRM и число увидевших условие в каждой группе для проверки симметрии триггера.
select
    experiment_id,
    count(*) filter (where grp = 'C') as n_c,
    count(*) filter (where grp = 'E') as n_e,
    count(*) filter (where grp = 'C' and experienced) as n_exp_c,
    count(*) filter (where grp = 'E' and experienced) as n_exp_e,
    count(could_see_video) > 0 as has_video_check
from exp_students
group by all
order by experiment_id;

-- name: trigger_263057
-- Единственный эксперимент, где не увидевшие условие есть только в одной группе.
select
    grp,
    experienced,
    complete,
    count(*) as n,
    min(problem_count) as min_problems,
    median(problem_count) as median_problems,
    max(problem_count) as max_problems
from exp_students
where experiment_id = 263057
group by all
order by all;

-- name: covariates
-- Строки учеников с ковариатами до эксперимента. Флаги Valid и индикаторы категорий строятся в Python.
select
    experiment_id,
    grp,
    experienced,
    could_see_video,
    prior_pct_correct,
    prior_pct_completion,
    z_mastery_speed,
    prior_hw_pct_completion,
    z_hw_mastery_speed,
    gender,
    state_id
from exp_students;

-- name: completion_by_sample
-- Завершившие по группам на всей выборке и среди увидевших условие.
select experiment_id, 'all' as sample, grp, count(*) as n, sum(complete) as n_done
from exp_students
group by all
union all
select experiment_id, 'experienced' as sample, grp, count(*) as n, sum(complete) as n_done
from exp_students
where experienced
group by all
order by experiment_id, sample, grp;

-- name: early_quitters
-- Проверка без флага experienced: есть ли в одной группе бросившие раньше, чем самый ранний бросивший в другой.
with quit as (
    select experiment_id, grp, problem_count from exp_students where complete = 0
),
first_quit as (
    select
        experiment_id,
        min(problem_count) filter (where grp = 'C') as min_c,
        min(problem_count) filter (where grp = 'E') as min_e
    from quit
    group by all
)
select
    experiment_id,
    count(*) filter (where grp = 'C') as n_quit_c,
    count(*) filter (where grp = 'E') as n_quit_e,
    min_c,
    min_e,
    count(*) filter (where grp = 'E' and problem_count < min_c) as n_e_before_c,
    count(*) filter (where grp = 'C' and problem_count < min_e) as n_c_before_e
from quit
join first_quit using (experiment_id)
group by all
order by experiment_id;

-- name: quit_position
-- На какой задаче бросили незавершившие, по группам.
select experiment_id, grp, problem_count, count(*) as n
from exp_students
where complete = 0
group by all
order by all;

-- name: early_completers_263057
-- Завершившие 263057 по числу задач: где условие уже сработало в E.
select grp, problem_count, experienced, count(*) as n
from exp_students
where experiment_id = 263057 and complete = 1 and problem_count < 10
group by all
order by all;

-- name: not_experienced_256027
-- Не увидевшие условие в 256027 по группам и завершению.
select grp, complete, count(*) as n, min(problem_count) as min_problems
from exp_students
where experiment_id = 256027 and not experienced
group by all
order by all;
