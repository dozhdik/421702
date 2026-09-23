SELECT DISTINCT sg.КодовыйНомерГруппы
FROM СТУДЕНЧЕСКАЯ_ГРУППА AS sg
JOIN ПРЕПОДАВАТЕЛЬ AS prep
ON prep.Специальность  LIKE '%' || sg.Специальность || '%'