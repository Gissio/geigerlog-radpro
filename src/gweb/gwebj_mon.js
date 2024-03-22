
// gwebj_mon.js

var myMinValue      = 0.8;
var myMaxValue      = 80000;
var powerGauge;
var usvvalue        = -99;
var sensitvalue     = -99;
var lastvalshown    = -99;

var VarIndex        = 0;
var oldVarIndex     = 0;


async function getVarIndex(){

    oldVarIndex = VarIndex;
    try         {VarIndex = document.getElementById("vars").selectedIndex;}
    catch(e)    {VarIndex = 0;}
    // console.log("VarIndex: ", VarIndex, "oldVarIndex: ", oldVarIndex)
}


function createPowerGauge(){
    // this only creates the instance; it does not render the graph

    let lt, ht;

    sensitvalue = LastData[VarNames[13 + VarIndex]];
    if (!isNaN(sensitvalue)){
        lt = LastData["limitLo"] * sensitvalue;
        ht = LastData["limitHi"] * sensitvalue;
    }
    else{
        lt = 0.5;
        ht = 0.5;
    }
    lt = clamp(lt, myMinValue, myMaxValue);
    ht = clamp(ht, myMinValue, myMaxValue);
    console.log("sensitvalue", sensitvalue, "lowthresh:", lt, "highthresh: ", ht);

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
    console.log("Colors: low: ", col1, "default: ", col2, "high: ", col3, "blue: ", col4);

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


async function updateGraph(VarIndex){

    let lastval, strlastCPM;

    getVarIndex();

    lastval = LastData[VarNames[1 + VarIndex * 2]];
    lastvalshown = lastval;

    if      (VarIndex == 0)    usvvalue = LastData["cpm"]    / LastData["sensitivityDef"];
    else if (VarIndex == 1)    usvvalue = LastData["cpm1st"] / LastData["sensitivity1st"];
    else if (VarIndex == 2)    usvvalue = LastData["cpm2nd"] / LastData["sensitivity2nd"];
    else if (VarIndex == 3)    usvvalue = LastData["cpm3rd"] / LastData["sensitivity3rd"];
    // // console.log("usvvalue: ", usvvalue)


    if (isNaN(lastval)) {strlastCPM = "---";}
    else                {strlastCPM = lastval.toFixed(0);}

    try {
        document.getElementById("cpm").innerHTML = strlastCPM;
        document.getElementById("cps").innerHTML = getNumFormat(lastval / 60);
        document.getElementById("usv").innerHTML = getNumFormat(usvvalue);
    }
    catch(e){}

    try {
        document.getElementById("temp"  ).innerHTML = getNumFormat(LastData["temp"]);
        document.getElementById("press" ).innerHTML = getNumFormat(LastData["press"]);
        document.getElementById("humid" ).innerHTML = getNumFormat(LastData["humid"]);
        document.getElementById("xtra"  ).innerHTML = getNumFormat(LastData["xtra"]);
    }
    catch(e){}

    powerGauge.update(lastval);

}


async function MonMain(){

    document.title = "Monitor";
    // document.getElementById("VariableName").textContent = "CPM";

    // set VarIndex and oldVarIndex
    getVarIndex();

    await getLastData();
    await getGeigerLogStatus();
    await setButtonStates();
    oldLogStatus = LogStatus;
    console.log("MonMain: LogStatus: ", LogStatus, "oldLogStatus: ", oldLogStatus)

    if (LogStatus){
        // show PowerGauge
        createPowerGauge();
        powerGauge.render("#gauge");
        updateGraph(VarIndex);
    }
    else{
        createPowerGauge();
        powerGauge.render("#gauge");
        // updateGraph(VarIndex);
    }

    // console.log("MonMain: powerGauge: min, max:", powerGauge.config.minValue, powerGauge.config.maxValue, "transitionMs:", powerGauge.config.transitionMs);

    setInterval(async function() {
        await getLastData();
        await getGeigerLogStatus();
        await setButtonStates();
        // console.log("MonMain: Interval LogStatus: ", LogStatus, "oldLogStatus: ", oldLogStatus)

        if (LogStatus) {
            getVarIndex();
            // console.log("MonMain: Interval VarIndex: ", VarIndex, "oldVarIndex: ", oldVarIndex)

            if (VarIndex != oldVarIndex){
                let lt, ht;
                sensitvalue = LastData[VarNames[13 + VarIndex]];
                if (!isNaN(sensitvalue)){
                    lt = LastData["limitLo"] * sensitvalue;
                    ht = LastData["limitHi"] * sensitvalue;
                }
                else{
                    lt = 0.5;
                    ht = 0.5;
                }
                // lt = clamp(lt / 60, myMinValue, myMaxValue);
                // ht = clamp(ht / 60, myMinValue, myMaxValue);
                lt = clamp(lt, myMinValue, myMaxValue);
                ht = clamp(ht, myMinValue, myMaxValue);
                console.log("sensitvalue", sensitvalue, "lowthresh:", lt, "highthresh: ", ht);
                let newconfig = {lowThreshhold: lt, highThreshhold:ht}
                powerGauge.setConfig(newconfig).render("#gauge");
            }
        }

        if (oldLogStatus != LogStatus) {
            oldLogStatus = LogStatus;
            console.log("removing svg")
            d3.selectAll("svg").remove();
            createPowerGauge();
            powerGauge.render("#gauge");
        }

        if (LogStatus) {
            await getLastData();
            updateGraph(VarIndex);
        }
        else{
            powerGauge.update(lastvalshown);
        }

        // updateGraph(VarIndex);

    }, MonRefresh);
}

MonMain();

