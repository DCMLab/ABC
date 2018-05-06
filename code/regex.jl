regex = r"""^
    (\.)?
    ((?P<key>[a-gA-G](b*|\#*)|(b*|\#*)(VII|VI|V|IV|III|II|I|vii|vi|v|iv|iii|ii|i))\.)?
    ((?P<pedal>(b*|\#*)(VII|VI|V|IV|III|II|I|vii|vi|v|iv|iii|ii|i))\[)?
    (?P<numeral>(b*|\#*)(VII|VI|V|IV|III|II|I|vii|vi|v|iv|iii|ii|i|Ger|It|Fr))
    (?P<form>[%o+M])?
    (?P<figbass>(9|7|65|43|42|2|64|6))?
    (\((?P<changes>(\+?(b*|\#*)\d)+)\))?
    (/\.?(?P<relativeroot>(b*|\#*)(VII|VI|V|IV|III|II|I|vii|vi|v|iv|iii|ii|i)))?
    (?P<pedalend>\])?
    (?P<phraseend>\\\\)?$
"""x
