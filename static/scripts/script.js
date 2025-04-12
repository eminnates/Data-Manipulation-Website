/*=============== BUTTON ===============*/
const dropdownContainers = document.querySelectorAll(".dropdown-button-container");

  dropdownContainers.forEach(container => {
    const button = container.querySelector(".dropdown-button");
    const options = container.querySelectorAll(".dropdown-content a");

    options.forEach(option => {
      option.addEventListener("click", (e) => {
        e.preventDefault();
        button.textContent = option.textContent;
      });
    });
  });

/*=============== FILE MENU ===============*/
let selectedFile = null;

// Dosya seçimi
document.getElementById("hiddenFileInput").addEventListener("change", function () {
  selectedFile = this.files[0];
});

document.getElementById("glowButton").addEventListener("click", () => {
  document.getElementById("hiddenFileInput").click();
});

// Dropdown seçimlerini buton metni olarak güncelle
document.querySelectorAll(".dropdown-button-container").forEach(container => {
  const button = container.querySelector(".dropdown-button");
  const options = container.querySelectorAll(".dropdown-content a");

  options.forEach(option => {
    option.addEventListener("click", (e) => {
      e.preventDefault();
      button.textContent = option.textContent;
    });
  });
});

// Çalıştır butonuna basınca her şeyi gönder
document.querySelector(".center-button").addEventListener("click", () => {
    const dropdownButtons = document.querySelectorAll(".dropdown-button");
    const projectTitle = document.querySelector(".textbox").value;
  
    if (!selectedFile) {
      alert("Lütfen bir dosya seçin.");
      return;
    }
  
    if (!projectTitle) {
      alert("Proje başlığı boş olamaz.");
      return;
    }
  
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("secim1", dropdownButtons[0].textContent);
    formData.append("secim2", dropdownButtons[1].textContent);
    formData.append("secim3", dropdownButtons[2].textContent);
  
    // 1. Adım: /upload/<projectName> çağrısı
    fetch(`/upload/${encodeURIComponent(projectTitle)}`, {
      method: "POST",
      body: formData
    })
    .then(response => {
      if (response.ok) {
        // 2. Adım: /run-script çağrısı
        return fetch('/run-script', { method: 'POST' });
      } else {
        return response.text().then(text => alert(text));
      }
    })
    .then(response => {
      if (response.ok) {
        // 3. Adım: /get-graph iframe içine yükle
        document.getElementById("resultFrame").src = "/get-graph";
      } else {
        return response.text().then(text => alert("Script çalıştırma başarısız: " + text));
      }
    })
    .catch(err => {
      console.error("Gönderim hatası:", err);
      alert("Bir hata oluştu.");
    });
  });
  

/*=============== SHOW MENU ===============*/
const showMenu = (toggleId, navId) =>{
    const toggle = document.getElementById(toggleId),
          nav = document.getElementById(navId)
 
    toggle.addEventListener('click', () =>{
        // Add show-menu class to nav menu
        nav.classList.toggle('show-menu')
 
        // Add show-icon to show and hide the menu icon
        toggle.classList.toggle('show-icon')
    })
 }
 
 showMenu('nav-toggle','nav-menu')
 /*=============== BUTTON STAR EFFECT ===============*/
 const glowButtons = document.querySelectorAll('.box button');
 let activeStars = [];

 glowButtons.forEach(button => {
     button.addEventListener("mouseover", () => {
         // Remove any existing stars
         removeAllStars();
         
         // Create new stars
         for (let i = 0; i < 5; i++) { 
             createStar(button);
         }
     });

     button.addEventListener("mouseleave", () => {
         removeAllStars();
     });
 });

 function createStar(button) {
     const star = document.createElement("div");
     star.classList.add("stars");
     if (Math.random() > 0.5) star.classList.add("large");
     document.body.appendChild(star);

     const buttonRect = button.getBoundingClientRect();
     const startX = Math.random() * buttonRect.width + buttonRect.left;
     const startY = Math.random() * buttonRect.height + buttonRect.top;
     
     star.style.left = `${startX}px`;
     star.style.top = `${startY}px`;

     setTimeout(() => {
         const angle = Math.random() * 2 * Math.PI;
         const distance = Math.random() * 50 + 20;
         const moveX = Math.cos(angle) * distance;
         const moveY = Math.sin(angle) * distance;
         star.style.transform = `rotate(45deg) translate(${moveX}px, ${moveY}px)`;
         star.style.opacity = "1";
     }, 50);
     
     activeStars.push(star);
 }

 function removeAllStars() {
     activeStars.forEach(star => {
         star.style.opacity = "0";
         setTimeout(() => star.remove(), 500);
     });
     activeStars = [];
 }