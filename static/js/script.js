// AI Predictive Maintenance
// Common JavaScript


console.log(
"AI Predictive Maintenance System Loaded"
);


// Auto hide alerts

setTimeout(()=>{


let alerts=document.querySelectorAll(".alert");


alerts.forEach(alert=>{

alert.style.display="none";

});


},4000);