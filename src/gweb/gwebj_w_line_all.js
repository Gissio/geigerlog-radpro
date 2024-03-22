
// js for d3 line: gwebj_w_line_all.js

var linedata;


async function getLineData(VarIndex, DeltaT) {

    const datalastrecs = await d3.csv("/lastrecs?var=" + String(VarIndex) + "&dt=" + String(DeltaT));
    // console.log("getLineData: all datalastrecs:\n", datalastrecs);
    // console.log("getLineData: last:", datalastrecs[datalastrecs.length -1]);

    linedata = [];
    for (let i = 0; i < datalastrecs.length; i++){
        linedata[i] = {"DateTime": new Date(datalastrecs[i]["DateTime"]), "Value": +datalastrecs[i]["Value"]};
    };
    // console.log("getLineData: linedata:", linedata)
};


function updateGraph(VarName, unit){

    let lastval, strval;

    makeLineGraph(linedata);

    try      {lastval = linedata[linedata.length - 1]["Value"];}
    catch(e) {lastval = 0;}
    // console.log("linedata[linedata.length - 1]['Value']", linedata[linedata.length - 1]["Value"]);

    if (VarName.startsWith("CP")){strval = lastval.toFixed(0);}
    else                         {strval = getNumFormat(lastval); }
    document.getElementById("varvalue").innerHTML = VarName + " : " + strval + unit;
    // console.log("VarName:", VarName, "Value:", strval, "Unit:", unit)
}


async function LineMain(){

    let unit = "";

    document.title = "Line";

    if      (VarName.startsWith("Temp"))    {unit = " °C"}
    else if (VarName.startsWith("Press"))   {unit = " hPa"}
    else if (VarName.startsWith("Humid"))   {unit = " %"}
    else if (VarName.startsWith("Xtra"))    {unit = " Units"}
    else if (VarName.startsWith("CPM"))     {unit = " CPM"}
    else if (VarName.startsWith("CPS"))     {unit = " CPS"}
    // console.log("VarName:", VarName, "Value:", strval, "Unit:", unit)

    await getLastData();
    await getGeigerLogStatus();
    // console.log("MonMain: Interval LogStatus: ", LogStatus, "oldLogStatus: ", oldLogStatus)

    if (LogStatus) {
        document.getElementById("linegraph").style.backgroundColor = '#ebebeb';
        await getLineData(VarIndex, DeltaT);
        updateGraph(VarName, unit);
    }
    else{
        document.getElementById("linegraph").style.backgroundColor = 'grey';
        await getLineData(VarIndex, DeltaT);
        updateGraph(VarName, unit);
        // document.getElementById("linegraph").innerHTML = "<br><br>Not Logging";
    }

    setInterval(async function() {
        await getLastData();
        await getGeigerLogStatus();
        console.log("gwebj_w_line_all.js:  DeltaT", DeltaT)
        if (LogStatus) {
            document.getElementById("linegraph").style.backgroundColor = '#ebebeb';
            await getLineData(VarIndex, DeltaT);
            d3.selectAll("svg").remove();
            updateGraph(VarName, unit);
        }
        else{
            document.getElementById("linegraph").style.backgroundColor = 'grey';
        }
    }, MonRefresh );
}

LineMain();

