document.addEventListener("DOMContentLoaded",()=>{

const form=document.getElementById("registro-form");

const password=document.getElementById("id_password1");
const confirm=document.getElementById("id_password2");
const button=document.getElementById("submit-btn");


// Barra de seguridad

const strength=document.createElement("div");
strength.className="strength";

const bar=document.createElement("div");

strength.appendChild(bar);

password.parentElement.appendChild(strength);


password.addEventListener("input",()=>{

let value=password.value;

let score=0;

if(value.length>=8)score++;
if(/[A-Z]/.test(value))score++;
if(/[0-9]/.test(value))score++;
if(/[^A-Za-z0-9]/.test(value))score++;

let width=["0%","25%","50%","75%","100%"][score];

let color=["#ddd","#ff4d4d","#ff9800","#ffc107","#2ecc71"][score];

bar.style.width=width;
bar.style.background=color;

});


// Mostrar contraseña

const eye=document.createElement("span");

eye.className="show-password";
eye.innerHTML="👁";

password.parentElement.appendChild(eye);

eye.onclick=()=>{

if(password.type==="password"){

password.type="text";
eye.innerHTML="🙈";

}else{

password.type="password";
eye.innerHTML="👁";

}

};


// Coincidencia

confirm.addEventListener("input",()=>{

if(confirm.value===""){

confirm.style.borderColor="#d7dce7";
return;

}

if(confirm.value===password.value){

confirm.style.borderColor="#2ecc71";

}else{

confirm.style.borderColor="#e74c3c";

}

});


// Animación botón

form.addEventListener("submit",()=>{

button.disabled=true;

button.innerHTML="Creando cuenta...";

});


// Animación focus

document.querySelectorAll(".field__input").forEach(input=>{

input.addEventListener("focus",()=>{

input.parentElement.style.transform="scale(1.02)";

});

input.addEventListener("blur",()=>{

input.parentElement.style.transform="scale(1)";

});

});

});