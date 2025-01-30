var originalTitle = document.title;
var blinkingInterval;
var isBlinking = false;
var currentBadgeCalls = 0;

function initializeAudio() {
    const audioButton = document.getElementById('init-audio');
    const notificationSound = document.getElementById('notification-sound');

    if (audioButton && notificationSound) {
        audioButton.click();
        notificationSound.play().catch(() => {
            // Если произошла ошибка, игнорируем её
        }).then(() => {
            notificationSound.pause();
            notificationSound.currentTime = 0;
        });
    }
}

function animateTitle(badgeCalls) {
    let counter = 0;
    const messages = [
        `У вас ${badgeCalls} новых звонков!`,
        `Проверьте новые звонки!`,
        `Не пропустите новые звонки!`
    ];
    currentBadgeCalls = badgeCalls;

    if (!isBlinking) {
        isBlinking = true;
        blinkingInterval = setInterval(() => {
            if (counter >= messages.length) {
                counter = 0;
            }
            document.title = messages[counter];
            counter++;
        }, 1000);

        // Возвращаем заголовок в исходное состояние при активации вкладки
        window.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                clearInterval(blinkingInterval);
                if (currentBadgeCalls > 0) {
                    document.title = `Звонки (${currentBadgeCalls})`;
                } else {
                    document.title = 'Звонки';
                }
                isBlinking = false;
            }
        });

        window.addEventListener('focus', () => {
            if (document.hasFocus()) {
                clearInterval(blinkingInterval);
                if (currentBadgeCalls > 0) {
                    document.title = `Звонки (${currentBadgeCalls})`;
                } else {
                    document.title = 'Звонки';
                }
                isBlinking = false;
            }
        });
    }
}

function handleHtmxResponse(badgeCalls) {
    try {
        const notificationSound = document.getElementById('notification-sound');
        notificationSound.play();
    } catch (err) {
        console.error("Playback was denied", err);
    }

    // Запускаем анимацию заголовка страницы
    animateTitle(badgeCalls);
}

window.addEventListener('DOMContentLoaded', (event) => {
    // Инициализируем звуковой файл при взаимодействии с документом
    document.body.addEventListener('click', initializeAudio, { once: true });
});

function animateTitle(badgeCalls) {
    let counter = 0;
    const messages = [
        `У вас ${badgeCalls} новых звонков!`,
        `Проверьте новые звонки!`,
        `Не пропустите новые звонки!`
    ];
    currentBadgeCalls = badgeCalls;

    if (!isBlinking) {
        isBlinking = true;
        blinkingInterval = setInterval(() => {
            if (counter >= messages.length) {
                counter = 0;
            }
            document.title = messages[counter];
            counter++;
        }, 1000);

        // Возвращаем заголовок в исходное состояние при активации вкладки
        window.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                clearInterval(blinkingInterval);
                if (currentBadgeCalls > 0) {
                    document.title = `Звонки (${currentBadgeCalls})`;
                } else {
                    document.title = 'Звонки';
                }
                isBlinking = false;
            }
        });

        window.addEventListener('focus', () => {
            if (document.hasFocus()) {
                clearInterval(blinkingInterval);
                if (currentBadgeCalls > 0) {
                    document.title = `Звонки (${currentBadgeCalls})`;
                } else {
                    document.title = 'Звонки';
                }
                isBlinking = false;
            }
        });
    }
}

function password_toggle(tag){
    const showPassword = document.querySelector(tag);
const passwordField = document.querySelector("#inputPassword5");
var state = false;
showPassword.onclick = function(){
    if (state){
        showPassword.classList.add('fa-eye');
        showPassword.classList.remove("fa-eye-slash");
        state = false;
    }
    else {
        showPassword.classList.remove('fa-eye');
        showPassword.classList.add("fa-eye-slash");
        state = true;
    }
    const type = passwordField.getAttribute("type") === "password" ? "text" : "password";
    passwordField.setAttribute("type", type)
}
}

function yuan_pattern(){
    var yuan = document.getElementById('yuan');
    var yuan_options = {
    mask: Number,  // enable number mask

    // other options are optional with defaults below
    scale: 2,  // digits after point, 0 for integers
    thousandsSeparator: '',  // any single char
    padFractionalZeros: false,  // if true, then pads zeros at end to the length of scale
    normalizeZeros: true,  // appends or removes zeros at ends
    radix: '.',  // fractional delimiter
    mapToRadix: ['.'],  // symbols to process as radix

    // additional number interval options (e.g.)
    min: -100,
    max: 100
};
var mask_yuan = IMask(yuan, yuan_options);
}

function yuan_non_cash_pattern(){
    var yuan = document.getElementById('yuan_non_cash');
    var yuan_options = {
    mask: Number,  // enable number mask

    // other options are optional with defaults below
    scale: 2,  // digits after point, 0 for integers
    thousandsSeparator: '',  // any single char
    padFractionalZeros: false,  // if true, then pads zeros at end to the length of scale
    normalizeZeros: true,  // appends or removes zeros at ends
    radix: '.',  // fractional delimiter
    mapToRadix: ['.'],  // symbols to process as radix

    // additional number interval options (e.g.)
    min: -100,
    max: 100
};
var mask_yuan = IMask(yuan, yuan_options);
}

function dollar_pattern(){
var dollar = document.getElementById('dollar');
var dollar_options = {
  mask: Number,  // enable number mask

  // other options are optional with defaults below
  scale: 2,  // digits after point, 0 for integers
  thousandsSeparator: '',  // any single char
  padFractionalZeros: false,  // if true, then pads zeros at end to the length of scale
  normalizeZeros: true,  // appends or removes zeros at ends
  radix: '.',  // fractional delimiter
  mapToRadix: ['.'],  // symbols to process as radix

  // additional number interval options (e.g.)
  min: -1000,
  max: 1000
};
var mask_dollar = IMask(dollar, dollar_options);
}

function phone_mask(){
var element = document.getElementById('phone-mask');
var maskOptions = {
            mask: '+{7} (000) 000-00-00'
};
var mask_phone = IMask(element, maskOptions);
}

function generatePassword() {
    var length = 12,
        charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        retVal = "";
    for (var i = 0, n = charset.length; i < length; ++i) {
        retVal += charset.charAt(Math.floor(Math.random() * n));
    }
    return retVal;
}

function RefreshPassClient(name){
var text_pass = document.getElementById(name);
var btn_refresh = document.getElementById("refresh-password-client");

btn_refresh.onclick = function() {
        text_pass.value = generatePassword();
}
}

function CopyPassClient(name){
var btn = document.getElementById("copy-password-client");

btn.onclick = function() {
      let textarea = document.createElement('textarea');
      textarea.id = 'temp';
      textarea.style.height = 0;
      document.body.appendChild(textarea);
      textarea.value = document.getElementById(name).value;
      let selector = document.querySelector('#temp');
      selector.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);

      var tooltip = document.getElementById("myTooltip");
      tooltip.innerHTML = "Скопировано";
}
}

function outFunc() {
  var tooltip = document.getElementById("myTooltip");
  tooltip.innerHTML = "Скопировать";
}


function integer_positive_pattern(MyId){
var field = document.getElementById(MyId);
var integer_options = {
    mask: Number,
    padFractionalZeros: false,  // if true, then pads zeros at end to the length of scale
    normalizeZeros: true,  // appends or removes zeros at ends
    radix: ',',  // fractional delimiter
    mapToRadix: ['.'],
    min: 0,
    max: 10000000000,
    thousandsSeparator: ' '
};
var mask_integer_positive = IMask(field, integer_options);
}

function dollar_positive_pattern(MyId){
IMask(
  document.getElementById(MyId),
  {
    mask: '$num',
    blocks: {
      num: {
        mask: Number,
        padFractionalZeros: false,  // if true, then pads zeros at end to the length of scale
        normalizeZeros: true,  // appends or removes zeros at ends
        radix: ',',  // fractional delimiter
        mapToRadix: ['.'],
        min: 0,
        max: 10000000000,
        thousandsSeparator: ' '
      }
    }
  }
)
}

function submit_any_form(MyForm)
{
    document.getElementById(MyForm).submit()
}
function imask_class_int(){
let element = document.querySelectorAll(".imask_int");
var integer_options = {
    mask: Number,
    padFractionalZeros: false,
    normalizeZeros: true,
    radix: ',',
    mapToRadix: ['.'],
    scale: 3,
    min: 0,
    max: 10000000000,
    thousandsSeparator: ''
};
for (let i = 0; i < element.length; i++){
        let mask = IMask(element[i], integer_options);
    }
}

function inn_mask(){
var element = document.getElementById('inn-mask');
var maskOptions = {
            mask: '0000000000'
};
var mask_phone = IMask(element, maskOptions);
}

function float_mask(){
let element = document.querySelectorAll(".float-mask");
var float_options = {
    mask: Number,
    padFractionalZeros: false,
    normalizeZeros: true,
    radix: ',',
    mapToRadix: ['.'],
    scale: 2,
    min: 0,
    max: 10000000000,
    thousandsSeparator: ''
};
for (let i = 0; i < element.length; i++){
        let mask = IMask(element[i], float_options);
    }
}