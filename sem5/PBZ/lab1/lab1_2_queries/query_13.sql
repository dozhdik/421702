SELECT DISTINCT spj.ПР
FROM SPJ
JOIN J
ON spj.ПР = j.ПР
JOIN S
ON spj.П = s.П
WHERE s.Город != j.Город