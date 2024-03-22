
// gwebj_w_tube.js

var myMinValue      = 0.8;
var myMaxValue      = 80000;
var powerGauge;
var LastData        = [];
var usvvalue        = -99;
var sensitvalue     = -99;
var lastvalshown    = -99;


// async function getLastData(){
async function setUSV(){

    if      (VarIndex == 0)  {sensitvalue = LastData["sensitivityDef"]; usvvalue = LastData["cpm"]    / sensitvalue;}
    else if (VarIndex == 2)  {sensitvalue = LastData["sensitivity1st"]; usvvalue = LastData["cpm1st"] / sensitvalue;}
    else if (VarIndex == 4)  {sensitvalue = LastData["sensitivity2nd"]; usvvalue = LastData["cpm2nd"] / sensitvalue;}
    else if (VarIndex == 6)  {sensitvalue = LastData["sensitivity3rd"]; usvvalue = LastData["cpm3rd"] / sensitvalue;}

    else if (VarIndex == 1)  {sensitvalue = LastData["sensitivityDef"]; usvvalue = LastData["cps"]    / sensitvalue * 60;}
    else if (VarIndex == 3)  {sensitvalue = LastData["sensitivity1st"]; usvvalue = LastData["cps1st"] / sensitvalue * 60;}
    else if (VarIndex == 5)  {sensitvalue = LastData["sensitivity2nd"]; usvvalue = LastData["cps2nd"] / sensitvalue * 60;}
    else if (VarIndex == 7)  {sensitvalue = LastData["sensitivity3rd"]; usvvalue = LastData["cps3rd"] / sensitvalue * 60;}
    // console.log("sensitvalue: ", sensitvalue)
    // console.log("usvvalue:    ", usvvalue)
}


function createPowerGauge(){
    // this only creates the instance; it does not render the graph

    let lt, ht;
    if (!isNaN(sensitvalue)){
        lt = LastData["limitLo"] * sensitvalue;
        ht = LastData["limitHi"] * sensitvalue;
    }
    else{
        lt = 0.5;
        ht = 0.5;
    }

    // adjust for CPM & CPS
    if (VarName.startsWith("CPS")){
        // myMinValue = myMinValue;   // -> 0.8
        myMaxValue = myMaxValue / 10; // -> 8000
        lt         = clamp(lt / 60, myMinValue, myMaxValue);
        ht         = clamp(ht / 60, myMinValue, myMaxValue);
    }
    else{
        lt = clamp(lt, myMinValue, myMaxValue);
        ht = clamp(ht, myMinValue, myMaxValue);
    }
    // console.log("sensitvalue", sensitvalue, "lowthresh:", lt, "highthresh: ", ht);

    let col1, col2, col3, col4;
    if (LogStatus){
        col1 = '#34a853';
        col2 = '#fbbc05';
        col3 = '#ea4335';
        col4 = "#4285f4";    // Google color blue
    }
    else{
        col1 = '#ccc';
        col2 = '#aaa';
        col3 = '#888';
        col4 = '#ccc';
    }
    // console.log("Colors: low: ", col1, "default: ", col2, "high: ", col3, "blue: ", col4);

    powerGauge = new Gauge({
        size                : 340,
        minValue            : myMinValue,
        maxValue            : myMaxValue,
        lowThreshhold       : lt,
        highThreshhold      : ht,
        majorTicks          : 8,  // is ignored when in logScale
        scale               : 'log',
        displayUnit         : 'CPM',
        transitionMs        : 200,
        lowThreshholdColor  : col1,
        defaultColor        : col2,
        highThreshholdColor : col3,
    });
}


function updateGraph(VarName){

    let lastval, strlastCPM, strlastCPS, strlastUSV;

    lastval = LastData[VarName.toLowerCase()];

    if (isNaN(lastval)) {
        strlastCPM = "---";
        strlastCPS = "---";
        strlastUSV = "---";
    }
    else{
        if (VarName.startsWith("CPM")){
            strlastCPM = lastval.toFixed(0);
            strlastCPS = getNumFormat(lastval / 60);
            strlastUSV = getNumFormat(usvvalue);
        }
        else { // CPS
            strlastCPM = (lastval * 60).toFixed(0);
            strlastCPS = lastval.toFixed(0);
            strlastUSV = lastval.toFixed(0);
        }
    }

    document.getElementById("cpm").innerHTML = strlastCPM;
    document.getElementById("cps").innerHTML = strlastCPS;
    document.getElementById("usv").innerHTML = strlastUSV;

    powerGauge.update(lastval);
    lastvalshown = lastval;
}


async function MonMain(){

    document.title = "Gauge Tube";
    document.getElementById("VariableName").textContent = String(VarName);

    await getLastData();
    setUSV();
    await getGeigerLogStatus();
    // console.log("MonMain: LogStatus: ", LogStatus, "oldLogStatus: ", oldLogStatus)

    oldLogStatus = LogStatus;
    createPowerGauge();
    powerGauge.render("#gauge");
    updateGraph(VarName);

    setInterval(async function() {
        await getLastData();
        setUSV();
        await getGeigerLogStatus();
        // console.log("MonMain: LogStatus: ", LogStatus, "oldLogStatus: ", oldLogStatus)

        if (oldLogStatus != LogStatus) {
            document.getElementById("gauge").innerHTML = "";
            d3.selectAll("svg").remove();
            createPowerGauge();
            powerGauge.render("#gauge");
            oldLogStatus = LogStatus;
        }

        if (LogStatus) {
            await getLastData();
            updateGraph(VarName);
        }
        else{
            powerGauge.update(lastvalshown);
        }
    }, MonRefresh);
}

MonMain();

