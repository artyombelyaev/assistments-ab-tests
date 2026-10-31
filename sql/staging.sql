-- raw - файл как есть, exp_students - очищенная таблица: одна строка - один ученик в одном эксперименте.
-- Пути к файлам приходят из Python в переменных csv_path и xlsx_path.

create or replace view raw as
select * from read_csv(getvariable('csv_path'), header = true, nullstr = ['', 'N/A']);

create or replace view exp_students as
select
    problem_set as experiment_id,
    problem_set_name as experiment_name,
    "User ID" as user_id,
    InferredCondition as grp,
    ExperiencedCondition as experienced,
    "Could See Video" as could_see_video,
    "Prior Problem Count" as prior_problem_count,
    "Prior Correct Count" as prior_correct_count,
    "Prior Percent Correct" as prior_pct_correct,
    "Class ID" as class_id,
    "Class Section ID" as class_section_id,
    nullif(nullif(replace("Class Grade", '"', ''), 'N/A'), '') as class_grade,
    "Teacher ID" as teacher_id,
    replace(replace("Guessed Gender", '"', ''), 'Uknown', 'Unknown') as gender,
    try_cast(nullif(replace(Birthyear, '"', ''), '') as integer) as birthyear,
    school_id,
    "District ID" as district_id,
    "State ID" as state_id,
    "Prior Assignments Assigned" as prior_assignments_assigned,
    "Prior Assignment Count" as prior_assignment_count,
    "Prior Completion Count" as prior_completion_count,
    "Prior Percent Completion" as prior_pct_completion,
    "Prior Class Percent Completion" as prior_class_pct_completion,
    "Z-Scored Mastery Speed" as z_mastery_speed,
    "Prior Homework Assigned" as prior_hw_assigned,
    "Prior Homework Count" as prior_hw_count,
    "Prior Homework Completion Count" as prior_hw_completion_count,
    "Prior Homework Percent Completion" as prior_hw_pct_completion,
    "Prior Class Homework Percent Completion" as prior_class_hw_pct_completion,
    "Z-Scored HW Mastery Speed" as z_hw_mastery_speed,
    complete,
    ProblemCount as problem_count,
    "log(count)" as log_count
from raw;
