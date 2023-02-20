html   : ws* elem+ ws*
       ;
elem   : "<" tagBody
       | "&" [A-Za-z]+ ";"
       | [\^<&]
       ;
tagBody: name attrib* ws* ">" 
       | "/" name ">"
       | "--" nonComEnd* "-->"
       | "!" [\^>]* ">"
       ;

nonComEnd : "-" nonComEnd2
          | [\^-]
          ;


nonComEnd2: [\^-] | "-" [\^>] ;

name   : [A-Za-z] [A-Za-z0-9_-]* 
       ;
ws     : [ \t\n]
       ;
attrib : ws+ name eqValue?
       ;
eqValue: "=" value?
       ;
value  : "'"  [\^']* "'" 
       | ["] [\^"]* ["]
       | [\^ "'`=<>]+ 
       ;
