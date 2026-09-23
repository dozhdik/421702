SELECT DISTINCT prep.Фамилия, pg.КодовыйНомерГруппы
FROM ПРЕПОДАВАТЕЛЬ AS prep
JOIN ПРЕПОДАВАТЕЛЬ_ПРЕПОДАЕТ_ПРЕДМЕТЫ_В_ГРУППАХ AS pg
ON prep.ЛичныйНомер = pg.ЛичныйНомер
WHERE prep.Фамилия = 'Фролов'