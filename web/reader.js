// Reader controls: which text to show, notes, scansion; copying verse links; section contents.
// Everything here is optional: the pages read fine without JavaScript.
(function () {
  "use strict";
  var root = document.documentElement;
  var KEY = "africa-view";
  var defaults = { text: "both", notes: "on", scan: "off", toc: "on" };

  function load() {
    var v = {};
    try { v = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) {}
    return { text: v.text || defaults.text, notes: v.notes || defaults.notes, scan: v.scan || defaults.scan, toc: v.toc || defaults.toc };
  }
  function save(v) {
    try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) {}
  }

  var view = load();
  var narrow = window.matchMedia("(max-width: 64rem)");
  var controls = document.querySelector(".controls");

  function apply() {
    root.dataset.text = view.text;
    root.dataset.notes = view.notes;
    root.dataset.scan = view.scan;
    root.dataset.toc = view.toc;
    if (!controls) return;
    controls.querySelectorAll("[data-set=text]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.value === view.text));
    });
    controls.querySelectorAll("[data-toggle]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(view[b.dataset.toggle] === "on"));
    });
  }

  if (controls) {
    controls.hidden = false;
    controls.addEventListener("click", function (ev) {
      var b = ev.target.closest("button");
      if (!b) return;
      if (b.dataset.set) view[b.dataset.set] = b.dataset.value;
      else if (b.dataset.toggle) view[b.dataset.toggle] = view[b.dataset.toggle] === "on" ? "off" : "on";
      else if (b.classList.contains("toc-open") && !narrow.matches) view.toc = view.toc === "on" ? "off" : "on";
      else return;
      change();
    });
  }
  apply();

  // re-apply the view, keeping the verse at the top of the screen in place while the layout changes
  function change() {
    var anchor = firstVisibleVerse();
    var before = anchor && anchor.getBoundingClientRect().top;
    apply();
    syncOpener();
    save(view);
    if (anchor) window.scrollBy(0, anchor.getBoundingClientRect().top - before);
  }

  function firstVisibleVerse() {
    var verses = document.querySelectorAll(".v");
    var top = (document.querySelector(".bar") || { offsetHeight: 0 }).offsetHeight;
    for (var i = 0; i < verses.length; i++) {
      if (verses[i].getBoundingClientRect().bottom > top) return verses[i];
    }
    return null;
  }

  // clicking a verse number puts its link in the address bar and copies "africa.B.N  url"
  var toast = document.querySelector(".toast");
  var toastTimer;
  function say(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.hidden = true; }, 2200);
  }
  var bookEl = document.querySelector(".book");
  var bookNum = bookEl && bookEl.dataset.book;
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest(".n");
    if (!a || !bookNum) return;
    var n = a.getAttribute("href").slice(1);
    var id = "africa." + bookNum + "." + n;
    var url = location.href.split("#")[0] + "#" + n;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(id + "  " + url).then(
        function () { say("已复制 " + id + " 及其链接"); },
        function () {}
      );
    }
  });

  // section contents: a column that can be folded away on wide screens, a drawer on narrow ones;
  // the section being read is marked in it
  var toc = document.getElementById("toc");
  if (!toc) return;
  var opener = document.querySelector(".toc-open");
  function setDrawer(open) {
    toc.classList.toggle("open", open);
    syncOpener();
  }
  function syncOpener() {
    if (!opener) return;
    var shown = narrow.matches ? toc.classList.contains("open") : view.toc === "on";
    opener.setAttribute("aria-expanded", String(shown));
  }
  if (opener) opener.addEventListener("click", function () { if (narrow.matches) setDrawer(!toc.classList.contains("open")); });
  narrow.addEventListener("change", function () { setDrawer(false); });
  syncOpener();
  toc.addEventListener("click", function (ev) { if (ev.target.closest("a")) setDrawer(false); });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape") setDrawer(false); });
  document.addEventListener("click", function (ev) {
    if (toc.classList.contains("open") && !toc.contains(ev.target) && ev.target !== opener) setDrawer(false);
  });

  var links = {};
  toc.querySelectorAll("a").forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
  var current;
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var a = links[en.target.id];
        if (!a || a === current) return;
        if (current) current.removeAttribute("aria-current");
        a.setAttribute("aria-current", "true");
        current = a;
        if (!toc.classList.contains("open") && toc.scrollHeight > toc.clientHeight) {
          var r = a.getBoundingClientRect(), t = toc.getBoundingClientRect();
          if (r.top < t.top || r.bottom > t.bottom) toc.scrollTop += r.top - t.top - t.height / 3;
        }
      });
    }, { rootMargin: "-20% 0px -70% 0px" });
    document.querySelectorAll(".sec").forEach(function (s) { io.observe(s); });
  }
})();
