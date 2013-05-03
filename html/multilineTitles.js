// source: 
// http://morecavalier.com/index.php?whom=Articles%2FMultiline+TITLES+for+Firefox

    var g_iCavTimer;
    var g_CarEle = null;
    var g_iCavDivLeft;
    var g_iCavDivTop;

    function SetCavTimer(evt)
    {
    	var e = (window.event) ? window.event : evt;
    	var src = (e.srcElement) ? e.srcElement : e.target;

    	g_iCavDivLeft = e.clientX - 2 + document.body.scrollLeft;
    	g_iCavDivTop = e.clientY + 19 + document.body.scrollTop;

    	window.clearTimeout(g_iCavTimer);
    	g_iCavTimer = window.setTimeout("ShowCavTitle()", 500);
    	g_CarEle = src;
    }

    function CancelCavTimer(evt)
    {
    	var e = (window.event) ? window.event : evt;
    	var src = (e.srcElement) ? e.srcElement : e.target;

    	var div = document.getElementById('cavTitleDiv');
    	if (div)
    		document.body.removeChild(div);

    	window.clearTimeout(g_iCavTimer);
    	g_CarEle = null;
    }

    function ShowCavTitle()
    {
    	for (var i = g_CarEle.attributes.length - 1; i >= 0; i--)
    	{
    		if (g_CarEle.attributes[i].name.toUpperCase() == 'CAVTITLE')
    		{
    			var div = document.getElementById('cavTitleDiv');
    			if (div)
    				break;

    			div = document.createElement("<DIV>");
    			div.id = 'cavTitleDiv';
    			div.style.position = 'absolute';
    			div.style.visibility = 'visible';
    			div.style.zIndex = 10;
			div.style.backgroundColor = 'yellow';
    			div.style.border = '1px solid black';
    			div.style.font = "normal normal normal 14pt normal 'Times New Roman'";

    			var sLeft = new String();
    			sLeft = g_iCavDivLeft.toString();
    			sLeft += 'px';
    			div.style.left = sLeft;
    			var sTop = new String();
    			sTop = g_iCavDivTop.toString();
    			sTop += 'px';
    			div.style.top = sTop;
    			
    			div.innerHTML = g_CarEle.attributes[i].value.split("\n").join("<br>").split(" ").join("&nbsp;");
    			document.body.appendChild(div);

    			var iWidth = div.scrollWidth + 10;
    			var sWidth = new String();
    			sWidth = iWidth.toString();
    			sWidth += 'px';
    			div.style.width = sWidth;

    			break;
    		}
    	}
    }
    	

