/*=============== SHOW MENU ===============*/
const showMenu = (toggleId, navId) => {
  const toggle = document.getElementById(toggleId),
      nav = document.getElementById(navId)

  toggle.addEventListener('click', () => {
      // Add show-menu class to nav menu
      nav.classList.toggle('show-menu')

      // Add show-icon to show and hide the menu icon
      toggle.classList.toggle('show-icon')
  })
}

showMenu('nav-toggle', 'nav-menu')
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


// Dropdown işlevselliği
const dropdown1 = document.getElementById('dropdown1');
const dropdown2 = document.getElementById('dropdown2');
const dropdown3 = document.getElementById('dropdown3');
const dropdown4 = document.getElementById('dropdown4');

// Dropdown seçenekleri için veri yapısı

const dropdownData = {
  Simple: {
    options: {
      Scatter: { columns: ['X', 'Y'], rows: ['Point A', 'Point B'] },
      Bar: { columns: ['Category', 'Value'], rows: ['Row A', 'Row B'] },
      Line: { columns: ['Time', 'Value'], rows: ['Series 1', 'Series 2'] },
      Area: { columns: ['Time', 'Value'], rows: ['Area 1', 'Area 2'] },
      Heatmap: { columns: ['X Axis', 'Y Axis'], rows: ['Heat A', 'Heat B'] },
      Table: { columns: ['Header 1', 'Header 2'], rows: ['Row 1', 'Row 2'] },
      Contour: { columns: ['X', 'Y'], rows: ['Contour 1', 'Contour 2'] },
      Pie: { columns: ['Label', 'Value'], rows: ['Slice A', 'Slice B'] }
    }
  },
  Distributions: {
    options: {
      Box: { columns: ['Variable'], rows: ['Group A', 'Group B'] },
      Violin: { columns: ['Measure'], rows: ['Class 1', 'Class 2'] },
      Histogram: { columns: ['Bins'], rows: ['Sample 1', 'Sample 2'] },
      '2D Histogram': { columns: ['X', 'Y'], rows: ['Group X', 'Group Y'] },
      '2D Contour Histogram': { columns: ['X', 'Y'], rows: ['Density 1', 'Density 2'] }
    }
  },
  "3D": {
    options: {
      '3D Scatter': { columns: ['X', 'Y', 'Z'], rows: ['Point A', 'Point B'] },
      '3D Line': { columns: ['X', 'Y', 'Z'], rows: ['Path 1', 'Path 2'] },
      '3D Surface': { columns: ['X', 'Y', 'Z'], rows: ['Surface A', 'Surface B'] },
      '3D Mesh': { columns: ['Vertex', 'Face'], rows: ['Mesh A', 'Mesh B'] },
      '3D Cone': { columns: ['Vector', 'Position'], rows: ['Cone A', 'Cone B'] },
      '3D Streamtube': { columns: ['Flow X', 'Flow Y', 'Flow Z'], rows: ['Tube A', 'Tube B'] }
    }
  },
  Maps: {
    options: {
      'Tile Map': { columns: ['Longitude', 'Latitude'], rows: ['Region A', 'Region B'] },
      'Atlas Map': { columns: ['Country', 'Value'], rows: ['Continent A', 'Continent B'] },
      'Choropleth Tile Map': { columns: ['Region', 'Intensity'], rows: ['Zone A', 'Zone B'] },
      'Choropleth Atlas Map': { columns: ['Region', 'Value'], rows: ['Area A', 'Area B'] },
      'Density Tile Map': { columns: ['Longitude', 'Latitude'], rows: ['Density A', 'Density B'] }
    }
  },
  Finance: {
    options: {
      Candlestick: { columns: ['Open', 'Close', 'High', 'Low'], rows: ['Stock A', 'Stock B'] },
      OHLC: { columns: ['Open', 'High', 'Low', 'Close'], rows: ['Stock X', 'Stock Y'] },
      Waterfall: { columns: ['Stage', 'Value'], rows: ['Step A', 'Step B'] },
      Funnel: { columns: ['Stage', 'Conversion'], rows: ['Step 1', 'Step 2'] },
      'Funnel Area': { columns: ['Stage', 'Value'], rows: ['Level A', 'Level B'] }
    }
  },
  Specialized: {
    options: {
      'Polar Scatter': { columns: ['Angle', 'Radius'], rows: ['Point A', 'Point B'] },
      'Polar Bar': { columns: ['Angle', 'Value'], rows: ['Bar A', 'Bar B'] },
      'Ternary Scatter': { columns: ['A', 'B', 'C'], rows: ['Mix 1', 'Mix 2'] },
      Sunburst: { columns: ['Label', 'Parent'], rows: ['Node A', 'Node B'] },
      Treemap: { columns: ['Label', 'Size'], rows: ['Block A', 'Block B'] },
      Sankey: { columns: ['Source', 'Target', 'Value'], rows: ['Flow A', 'Flow B'] }
    }
  }
};

// Temizleme fonksiyonu
function clearDropdown(dropdown) {
  dropdown.innerHTML = '<option value="">Seçim Yapın</option>';
  dropdown.disabled = false;
}

// Doldurma fonksiyonu
function populateDropdown(dropdown, options) {
  dropdown.innerHTML = '<option value="">Seçim Yapın</option>';
  options.forEach(option => {
    const opt = document.createElement('option');
    opt.value = option;
    opt.textContent = option;
    dropdown.appendChild(opt);
  });
  dropdown.disabled = false;
}


// İlk dropdown (kategori)
dropdown1.addEventListener('change', function () {
  clearDropdown(dropdown2);
  clearDropdown(dropdown3);
  clearDropdown(dropdown4);

  const selectedCategory = this.value;
  console.log('Selected Category:', selectedCategory);
  console.log('Available Categories:', Object.keys(dropdownData));
  
  if (selectedCategory && dropdownData[selectedCategory]) {
    const chartTypes = Object.keys(dropdownData[selectedCategory].options);
    populateDropdown(dropdown2, chartTypes);
  } else {
    console.log('Invalid category selected or category not found in dropdownData');
  }
});
// İkinci dropdown (grafik tipi)
dropdown2.addEventListener('change', function () {
  clearDropdown(dropdown3);
  clearDropdown(dropdown4);

  // Fix: Use value instead of text
  const category = dropdown1.value;
  const chart = this.value;

  if (category && chart && dropdownData[category] && dropdownData[category].options[chart]) {
    const config = dropdownData[category].options[chart];

    if (config.columns) {
      populateDropdown(dropdown3, config.columns);
    }

    if (config.rows) {
      populateDropdown(dropdown4, config.rows);
    }
  }
});

// Mobil menü işlevselliği
const navMenu = document.getElementById('nav-menu');
const navToggle = document.getElementById('nav-toggle');
const navClose = document.querySelector('.nav__close');



// Star efekti fonksiyonu
function createStar(event, button) {
  const star = document.createElement('div');
  star.className = 'stars';
  if (Math.random() > 0.5) star.classList.add('large');
  
  const rect = button.getBoundingClientRect();
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;
  
  star.style.left = centerX + 'px';
  star.style.top = centerY + 'px';
  
  document.body.appendChild(star);
  
  const angle = Math.random() * Math.PI * 2;
  const distance = Math.random() * 100 + 50;
  const duration = Math.random() * 0.5 + 0.5;
  
  star.style.transform = `translate(${Math.cos(angle) * distance}px, ${Math.sin(angle) * distance}px) rotate(45deg)`;
  star.style.opacity = '0';
  star.style.transition = `all ${duration}s ease-out`;
  
  setTimeout(() => star.remove(), duration * 1000);
}

// Butonlara star efekti ekleme
document.querySelectorAll('#glowButton, .run-button').forEach(button => {
  button.addEventListener('mouseover', (e) => {
      for (let i = 0; i < 5; i++) {
          setTimeout(() => createStar(e, button), i * 100);
      }
  });
});


/*=============== GÖNDER & POLLING ===============*/

document.querySelector(".run-button").addEventListener("click", () => {
  const dropdownButtons = document.querySelectorAll(".custom-dropdown");
  const projectTitle = document.querySelector(".custom-textbox").value;

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
  formData.append("secim4", dropdownButtons[3].textContent);

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

