SELECT П 
FROM S
WHERE Статус < (
	SELECT Статус
	FROM S
	WHERE П = 'П1'
)