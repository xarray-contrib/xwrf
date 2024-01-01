console.log("RUNNING CUSTOM JAVASCRIPT");

function getBodyThemeName() {
  var bodyTheme = document.body.dataset.theme;
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

  if (bodyTheme === "auto") {
    if (prefersDark) {
      bodyTheme = "dark";
    } else {
      bodyTheme = "light";
    }
  }

  return bodyTheme;
}

document.documentElement.setAttribute("theme", getBodyThemeName());

var observer = new MutationObserver(function (mutations) {
  mutations.forEach(function (mutation) {
    if (mutation.type == "attributes") {
      var bodyTheme = getBodyThemeName();
      console.log("document.body.dataset.theme changed to " + bodyTheme);
      document.documentElement.setAttribute("theme", bodyTheme);
    }
  });
});

observer.observe(document.body, { attributeFilter: ["data-theme"] });
