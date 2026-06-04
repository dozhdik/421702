%monkey_banana.pl
%//////////////////////////////////////////
%Лабораторная работа №2 по дисциплине ЛОИС
%Выполнена студентом группы 421702 БГУИР Дождиковым Александром Игоревичем
%Модуль нацелен на решение задачи планирования действий "Обезьяна и банан".
%02.05.2026
%
%Ссылки на использованные источники
/*   [1] SWI-Prolog. SWI-Prolog documentation [Электронный ресурс] : library(assoc) – Association lists (AVL trees). 
 *   – Режим доступа: https://www.swi-prolog.org/pldoc/doc_for?object=section(%27packages/assoc.html%27). 
 *   – Дата доступа: 08.05.2026.
 */
/*   [2] Реализация поиска в ширину (BFS) и управление состоянием в Prolog [Электронный ресурс] : Habr : IT-платформа. 
 *   – Режим доступа: https://habr.com/ru/articles/468335/. 
 *   – Дата доступа: 08.05.2026.
 */

:- use_module(library(assoc)).
:- dynamic puddle/2.

banana(3, 3).

in_bounds(X, Y) :- between(1, 5, X), between(1, 5, Y).
passable(X, Y)  :- in_bounds(X, Y), \+ puddle(X, Y).

action(state(MX,MY,BxX,BxY,StX,StY,HS,no),
       walk(NX,NY),
       state(NX,NY,BxX,BxY,StX,StY,HS,no)) :-
    member(DX-DY,[1-0,-1-0,0-1,0-(-1)]),
    NX is MX+DX, NY is MY+DY,
    passable(NX,NY).

action(state(MX,MY,MX,MY,StX,StY,HS,no),
       push_box(NBX,NBY),
       state(MX,MY,NBX,NBY,StX,StY,HS,no)) :-
    member(DX-DY,[1-0,-1-0,0-1,0-(-1)]),
    NBX is MX+DX, NBY is MY+DY,
    passable(NBX,NBY).

action(state(MX,MY,BxX,BxY,MX,MY,no,OB),
       grab_stick,
       state(MX,MY,BxX,BxY,MX,MY,yes,OB)).

action(state(MX,MY,MX,MY,StX,StY,HS,no),
       climb_box,
       state(MX,MY,MX,MY,StX,StY,HS,yes)).

action(state(MX,MY,MX,MY,_,_,yes,yes),
       get_banana,
       done) :- banana(MX,MY).

solve(Init, Path) :-
    empty_assoc(Empty),
    put_assoc(Init, Empty, 1, Visited0),
    bfs([[Init,[]]], Visited0, RevPath),
    reverse(RevPath, Path).

bfs([[State,Actions]|_], _, [get_banana|Actions]) :-
    action(State, get_banana, done), !.

bfs([[State,Actions]|Rest], Visited, Solution) :-
    findall(
        [Next,[Act|Actions]],
        (
            action(State, Act, Next),
            Next \= done,
            \+ get_assoc(Next, Visited, _)
        ),
        Children
    ),
    foldl([Child,V0,V1]>>(Child=[S,_], put_assoc(S,V0,1,V1)),
          Children, Visited, Visited1),
    append(Rest, Children, NewQueue),
    bfs(NewQueue, Visited1, Solution).

% ============================================================
%  QUERY EXAMPLES
%
%  Example 1 - basic:
%  ?- solve(state(1,1,1,1,5,5,no,no), Path), maplist(writeln, Path).
%
%  Expected: push box toward (3,3), walk to stick, grab_stick,
%            walk back, climb_box, get_banana
%
%  Example 2 - monkey already near box and stick:
%  ?- solve(state(3,2,3,2,3,1,no,no), Path), maplist(writeln, Path).
%
%  Expected: walk(3,1), grab_stick, walk(3,2),
%            push_box(3,3), walk(3,3), climb_box, get_banana
%
%  Example 3 - puddles blocking direct path:
%  ?- assertz(puddle(2,3)), assertz(puddle(3,2)),
%     solve(state(1,1,1,1,5,5,no,no), Path), maplist(writeln, Path).
%
%  Expected: detour around puddles, longer but valid path
% ============================================================
%assertz(puddle(2,3)), assertz(puddle(3,2)), solve(state(1,1,1,1,5,5,no,no), Path), maplist(writeln, Path).