stream: line+;

line: cmdline "\n" ;

pipeline: blankUnit* [ \t]* pipeline2* ;
pipeline2: "|" blankUnit* [ \t]* ;

cmdline: pipeline cmdline2* ;
cmdline2: ";" pipeline ; 

-unit: sinString | dblString | rawWord;

blankUnit: [ \t]* unit;

+rawWord: cpoint+;
cpoint: "\\" [ \t\n$'"\\] | [\^\\$'| \t\n";] ;
+sinString: ['] [\^']* ['] ;
+dblString: ["] dblInside* ["] ;
dblInside: escapeDbl | "$" [a-zA-Z]+ | [\^"\\$]* ;
escapeDbl: "\\" [$\\"] ;
