document.addEventListener("DOMContentLoaded",()=>{

    const inputs=document.querySelectorAll(".form-input");

    inputs.forEach(input=>{

        input.addEventListener("focus",()=>{

            input.parentElement.classList.add("active");

        });

        input.addEventListener("blur",()=>{

            if(input.value===""){

                input.parentElement.classList.remove("active");

            }

        });

    });

    const form=document.querySelector("form");

    form.addEventListener("submit",()=>{

        const btn=document.querySelector(".btn-primary");

        btn.disabled=true;
        btn.innerHTML="Ingresando...";

    });

});