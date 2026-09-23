SELECT DISTINCT spj.Д
FROM SPJ AS spj
JOIN S AS s
ON spj.П = s.П
WHERE s.Город = 'Лондон' 