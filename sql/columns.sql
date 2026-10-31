-- name: profile
-- Тип по выводу DuckDB и доля NULL. "N/A" и пустая строка читаются как NULL.
select column_name, column_type, null_percentage
from (summarize raw);

-- name: string_placeholders
-- В трёх строковых колонках значения обёрнуты в кавычки, и пропуск записан строкой, а не пустым полем.
select
    count(*) filter (where "Class Grade" = '"N/A"') as class_grade_na,
    count(*) filter (where Birthyear = '""') as birthyear_empty,
    count(*) filter (where "Guessed Gender" = '"Uknown"') as gender_uknown,
    count(*) as n
from raw;
