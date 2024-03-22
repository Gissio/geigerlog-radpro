
// gwebj_common.js
'use strict';

var MonRefresh    = 1000;  // ms
var LastData      = [];
var LogStatus     = 0;
var oldLogStatus  = 0;
var FileStatus    = 0;
var VarNames      = ["datetime",
                     "cpm",     "cps",      "cpm1st",   "cps1st",
                     "cpm2nd",  "cps2nd",   "cpm3rd",   "cps3rd",
                     "temp",    "press",    "humid",    "xtra",
                     "sensitivityDef", "sensitivity1st", "sensitivity2nd", "sensitivity3rd",
                     "limitLo", "limitHi",
                     "logstate", "filestate",
                     "TopWidget", "BottomWidget",
                    ];
var DeltaT        = MONSERVER_REC_LENGTH;           // min

var oldTopVarIndex      ;
var TopVarIndex         ;
var oldBottomVarIndex   ;
var BottomVarIndex      ;


SUPPRESSCONSOLELOG  

function BusyCursor()       {document.body.style.cursor = 'wait';}
function NormalCursor()     {document.body.style.cursor = 'default';}
function isNumber(value)    {return typeof value === 'number' && isFinite(value);}


// used for 1-line record types: lastdata, lastavg, ...
async function fetchRecord(RecordType){
    let fetchDataText = "";
    try{
        const fetchData = await fetch(RecordType, {cache: "no-store"});
        fetchDataText   = await fetchData.text();
        // console.log("fetchDataText", fetchDataText);

        if (fetchDataText.startsWith("<!")) fetchDataText = "HTML";
    }
    catch(error){
        console.log("Error:", error, " -- function: fetchRecord: RecordType:", RecordType);
    }
    return fetchDataText.split(",");
}


function getNumFormat(number){
    if      (isNaN(number))   return "---";
    else if (number >= 10000) return number.toFixed(0);
    else if (number >= 900)   return number.toFixed(1); // to allow P from 900.0 to >1030.9
    else if (number >= 100)   return number.toFixed(1);
    else                      return number.toFixed(2);
}


function clamp(val, minval, maxval){
    return Math.min(Math.max(val, minval), maxval);
}


async function getLastData(){

    const DataList = await fetchRecord('/lastdata');
    // console.log("DataList:", DataList);

    LastData[VarNames[0]] = new Date(DataList[0]);
    for (let i = 1; i < VarNames.length; i++){
        LastData[VarNames[i]] = +DataList[i];
    }
    // console.log("LastData:", LastData);
    // console.log("LastData.length:", LastData.length);
}


async function getGeigerLogStatus(){

    LogStatus  = LastData["logstate"];
    FileStatus = LastData["filestate"];

    if (LogStatus  === undefined) LogStatus  = 0;
    if (FileStatus === undefined) FileStatus = 0;
    // console.log("getGeigerLogStatus:  LogStatus", LogStatus, "FileStatus", FileStatus)

    TopVarIndex    = LastData["TopWidget"];
    BottomVarIndex = LastData["BottomWidget"];

    if (TopVarIndex    === undefined) TopVarIndex    = 0;
    if (BottomVarIndex === undefined) BottomVarIndex = 1;
    // console.log("getGeigerLogStatus:  TopVarIndex", TopVarIndex, "BottomVarIndex", BottomVarIndex)
}


async function setButtonStates(){

    if (LogStatus){
        document.getElementById("btnquick").disabled = true;
        document.getElementById("btnstart").disabled = true;
        document.getElementById("btnstop") .disabled = false;
    }
    else if(!LogStatus && FileStatus){
        document.getElementById("btnquick").disabled = false;
        document.getElementById("btnstart").disabled = false;
        document.getElementById("btnstop") .disabled = true;
    }
    else{
        document.getElementById("btnquick").disabled = false;
        document.getElementById("btnstart").disabled = true;
        document.getElementById("btnstop") .disabled = true;
    }
}

