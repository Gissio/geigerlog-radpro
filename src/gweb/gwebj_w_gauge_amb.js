
// gwebj_w_gauge_amb.js

var myMinValue      = 0.8;
var myMaxValue      = 80000;
var powerGauge;
var usvvalue        = -99;
var sensitvalue     = -99;
var lastvalshown    = -99;

function createPowerGauge(){
    // this only creates the instance; it does not render the graph

    // console.log("createPowerGauge: ")

    let lt, ht;
    // not used for amb vars:
    //     sensitvalue = LastAvgData[VarNames[13 + VarIndex]];
    //     if (!isNaN(sensitvalue)){
    //         lt = LastAvgData["limitLo"] * sensitvalue;
    //         ht = LastAvgData["limitHi"] * sensitvalue;
    //     }
    //     else{
    //         lt = 0.5;
    //         ht = 0.5;
    //     }
    lt = myMaxValue;
    ht = myMaxValue;
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
        scale               : 'lin',
        displayUnit         : 'None',
        transitionMs        : 200,
        lowThreshholdColor  : col4,
        defaultColor        : col2,
        highThreshholdColor : col3,
    });
}


function updateGraph(VarName, unit){

    let varpointer = +VarIndex;
    let lastval    = getNumFormat(LastData[VarNames[1 + varpointer]]);

    document.getElementById("varvalue").innerHTML = VarName + " : " + lastval + unit;
    powerGauge.update(lastval);
    lastvalshown = lastval;
}


async function MonMain(){

    let unit = "";

    document.title = "Gauge Ambient";

    if      (VarName.startsWith("Temp"))    {unit = " °C";      myMinValue = 0;     myMaxValue = 60;}
    else if (VarName.startsWith("Press"))   {unit = " hPa";     myMinValue = 970;   myMaxValue = 1030;}
    else if (VarName.startsWith("Humid"))   {unit = " %";       myMinValue = 0;     myMaxValue = 100;}
    else if (VarName.startsWith("Xtra"))    {unit = " Units";   myMinValue = -100;  myMaxValue = 100;}
    else if (VarName.startsWith("CPM"))     {unit = " CPM";     myMinValue = 0;     myMaxValue = 60;}
    else if (VarName.startsWith("CPS"))     {unit = " CPS";     myMinValue = 0;     myMaxValue = 60;}
    // console.log("unit: ", unit)

    await getLastData();
    await getGeigerLogStatus();
    // console.log("MonMain: LogStatus: ", LogStatus, "oldLogStatus: ", oldLogStatus)

    if (LogStatus) {
        oldLogStatus = LogStatus;
        document.getElementById("gauge").style.backgroundColor = "#ebebeb";
        createPowerGauge();
        powerGauge.render("#gauge");
        updateGraph(VarName, unit);
    }
    else{
        createPowerGauge();
        powerGauge.render("#gauge");
        updateGraph(VarName, unit);
    }

    setInterval(async function() {
        await getLastData();
        await getGeigerLogStatus();
        // console.log("MonMain: Interval LogStatus: ", LogStatus, "oldLogStatus: ", oldLogStatus)

        if (oldLogStatus != LogStatus) {
            oldLogStatus = LogStatus;
            if (LogStatus) {
                let col4 = "#4285f4";
                let newconfig = {lowThreshholdColor  : col4, defaultColor: col4, highThreshholdColor : col4}
                powerGauge.setConfig(newconfig).render("#gauge");
            }
            else{
                let col4 = "#ccc";
                let newconfig = {lowThreshholdColor  : col4, defaultColor: col4, highThreshholdColor : col4}
                powerGauge.setConfig(newconfig).render("#gauge");
                powerGauge.update(lastvalshown);
            }
        }

        if (LogStatus) {
            updateGraph(VarName, unit);
        }
    }, MonRefresh);
}

MonMain();

