
// js for Web Page Plot (2 iframes with line graphs)

async function getVarIndexes(){
    // reads the settings of the drop down box on the web page

    try         {TopVarIndex = document.getElementById("topvar").selectedIndex;}
    catch(e)    {TopVarIndex = 99;}

    try         {BottomVarIndex = document.getElementById("bottomvar").selectedIndex;}
    catch(e)    {BottomVarIndex = 99;}

    console.log("Indexes: Top: ", TopVarIndex, "oldTop: ", oldTopVarIndex, "Bottom: ", BottomVarIndex, "oldBottom: ", oldBottomVarIndex)
}


async function Graph2Main(){

    let newimg;

    document.title = "Plot";

    await getLastData();
    await getGeigerLogStatus();
    await setButtonStates();
    // await getVarIndexes(); // muss weg, sonst kein default setting

    document.getElementById("reclen").innerHTML = DeltaT + " min"

    oldTopVarIndex    = TopVarIndex;
    oldBottomVarIndex = BottomVarIndex;
    // console.log("TopVarIndex", TopVarIndex)

    document.getElementById("topvar").selectedIndex = TopVarIndex;
    newimg = "/widget_line?var=" + String(TopVarIndex);
    document.getElementById("iframetop").src = newimg;

    document.getElementById("bottomvar").selectedIndex = BottomVarIndex;
    newimg = "/widget_line?var=" + String(BottomVarIndex);
    document.getElementById("iframebottom").src = newimg;

    setInterval(async function() {
        await getLastData();
        await getGeigerLogStatus();
        await setButtonStates();
        await getVarIndexes();

        if (oldTopVarIndex != TopVarIndex){
            oldTopVarIndex = TopVarIndex;
            document.getElementById("topvar").selectedIndex = TopVarIndex;
            newimg = "/widget_line?var=" + String(TopVarIndex);
            document.getElementById("iframetop").src = newimg;
        }
        if (oldBottomVarIndex != BottomVarIndex){
            oldBottomVarIndex = BottomVarIndex;
            document.getElementById("bottomvar").selectedIndex = BottomVarIndex;
            newimg = "/widget_line?var=" + String(BottomVarIndex);
            document.getElementById("iframebottom").src = newimg;
        }
    }, MonRefresh);
}

Graph2Main();

