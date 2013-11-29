// ----------------------------------------------------------------------------
// markItUp!
// ----------------------------------------------------------------------------
// Copyright (C) 2008 Jay Salvat
// http://markitup.jaysalvat.com/
// ----------------------------------------------------------------------------
mySettings = {
    nameSpace:          'markdown', // Useful to prevent multi-instances CSS conflict
    previewParserPath:  '/recipes/markdownpreview/',
    onShiftEnter:       {keepDefault:false, openWith:'\n\n'},
    markupSet: [
        {name:'Titel', key:"1", openWith:'#### ', placeHolder:'Typ hier een titel...' },
        {name:'Vetgedrukt', key:"B", openWith:'**', closeWith:'**'},
        {name:'Schuingedrukt', key:"I", openWith:'_', closeWith:'_'},
        {separator:'---------------' },
        {name:'Ongenummerde lijst', openWith:'- ' },
        {name:'Genummerde lijst', openWith:function(markItUp) {
            return markItUp.line+'. ';
        }},
        {separator:'---------------'},
        {name:'Toon/verberg voorbeeld', call:'preview', className:"preview"}
    ]
}