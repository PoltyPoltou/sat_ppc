int: groups=15;
int: size=4;
int: weeks=6;
int: golfers= groups*size;
set of int: WEEK = 1..weeks;
set of int: GROUP = 1..groups;
set of int: SIZE = 1..size;
set of int: GOLFERS = 1..golfers;

array[WEEK,GROUP] of var set of GOLFERS: schedule;

constraint forall(g in GROUP) (
    schedule[1,g] = 1+size*(g-1)..size*g
);


constraint forall(w in WEEK, g in GROUP) (
    if g!=groups
    then
        min(schedule[w,g]) < min(schedule[w,g+1])
    endif
);

constraint forall(w in WEEK) (
    if w!=weeks
    then
        max(schedule[w,1]) < max(schedule[w+1,1])
    endif
);


constraint forall(w in WEEK, g in GROUP) (
    card(schedule[w,g]) = size
);

constraint forall(w in WEEK, g1 in GROUP, g2 in GROUP) (
    if g1<g2
    then
        schedule[w,g1] intersect schedule[w,g2] = {}
    endif
);

constraint forall(w1 in WEEK, w2 in WEEK, g1 in GROUP, g2 in GROUP) (
    if w1<w2
    then
        card(schedule[w1,g1] intersect schedule[w2,g2]) < 2
    endif
);


solve satisfy;

output [ show(schedule[i,j]) ++ " " ++
         if j == groups then "\n" else "" endif |
         i in WEEK, j in GROUP ];