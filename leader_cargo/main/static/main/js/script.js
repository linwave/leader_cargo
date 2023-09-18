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