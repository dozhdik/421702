SELECT DISTINCT *
FROM ПРЕПОДАВАТЕЛЬ
WHERE ЛичныйНомер IN (
	SELECT pg.ЛичныйНомер
	FROM ПРЕПОДАВАТЕЛЬ_ПРЕПОДАЕТ_ПРЕДМЕТЫ_В_ГРУППАХ AS pg
	WHERE pg.КодовыйНомерГруппы IN ('3Г', '8Г')
	GROUP BY pg.ЛичныйНомер
	HAVING count(DISTINCT pg.КодовыйНомерГруппы) = 2
)
AND Должность = 'Доцент'