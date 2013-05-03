function xstooltip_show(tooltipId, parentId, posX, posY)
{
    it = document.getElementById(tooltipId);
    img = document.getElementById(parentId);
    // if tooltip is too wide, shift left to be within parent 
    // if(posX + it.offsetWidth > img.offsetWidth) 
    //  posX -= it.offsetWidth;
    //if (posX < 0 ) posX = 0; 
    it.style.left = posX + 'px';
    it.style.top = posY + 'px';
    it.style.visibility = 'visible'; 
}


function xstooltip_hide(id)
{
    it = document.getElementById(id); 
    it.style.visibility = 'hidden'; 
}

function xstooltip_click(id, href)
{
    it = document.getElementById(id); 
    it.style.visibility = 'hidden'; 
    document.location.href = href;
    return false;
}
