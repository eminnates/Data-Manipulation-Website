/*=============== BUTTON ===============*/
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

/*=============== FILE MENU ===============*/
let selectedFile = null;

document.getElementById("hiddenFileInput").addEventListener("change", function () {
  selectedFile = this.files[0];
  const validExtensions = ['csv', 'xlsx', 'xml', 'json'];
  const fileExtension = selectedFile.name.split('.').pop().toLowerCase();

  if (!validExtensions.includes(fileExtension)) {
    alert("Geçersiz dosya formatı. Lütfen csv, xlsx, xml veya json dosyası seçin.");
    this.value = '';
  }
});

document.getElementById("glowButton").addEventListener("click", () => {
  document.getElementById("hiddenFileInput").click();
});

/*=============== GÖNDER & POLLING ===============*/
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

  fetch(`/upload/${encodeURIComponent(projectTitle)}`, {
    method: "POST",
    body: formData
  })
    .then(response => {
      if (response.ok) {
        return fetch('/run/run-script', { method: 'POST' });
      } else {
        return response.text().then(text => alert(text));
      }
    })
    .then(response => {
      if (response.ok) {
        let attempts = 0;
        const maxAttempts = 30;
        const interval = setInterval(() => {
          fetch("/graph/get-graph", { method: "HEAD" })
            .then(res => {
              if (res.ok) {
                // Dosya hazır, sadece 1 kez iframe'e yükle
                document.getElementById("resultFrame").src = "/graph/get-graph";
                clearInterval(interval);
              } else {
                attempts++;
                if (attempts >= maxAttempts) {
                  clearInterval(interval);
                  alert("Grafik oluşturulamadı.");
                }
              }
            })
            .catch(err => {
              console.error("Polling hatası:", err);
              clearInterval(interval);
              alert("Bir hata oluştu.");
            });
        }, 2000);
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
const showMenu = (toggleId, navId) => {
  const toggle = document.getElementById(toggleId),
    nav = document.getElementById(navId);

  toggle.addEventListener('click', () => {
    nav.classList.toggle('show-menu');
    toggle.classList.toggle('show-icon');
  });
};
showMenu('nav-toggle', 'nav-menu');

/*=============== BUTTON STAR EFFECT ===============*/
const glowButtons = document.querySelectorAll('.box button');
let activeStars = [];

glowButtons.forEach(button => {
  button.addEventListener("mouseover", () => {
    removeAllStars();
    for (let i = 0; i < 5; i++) createStar(button);
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

  const rect = button.getBoundingClientRect();
  star.style.left = `${Math.random() * rect.width + rect.left}px`;
  star.style.top = `${Math.random() * rect.height + rect.top}px`;

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
