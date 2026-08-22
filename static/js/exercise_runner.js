/*
 * SkillSprint Academy — interactive exercise runner (plan §4).
 *
 * Boots vendored Pyodide on demand and exposes `window.runPython(code)` to
 * the per-kind exercise templates. Also provides small framework helpers
 * for quiz_interactive, regex_lab, cipher_lab, pcap_challenge, and
 * binary_inspector widgets.
 *
 * Required by templates/exercises/*.html  and ContentItem rows whose
 * `exercise_spec.kind` matches one of the supported types.
 */

window.SkillSprintExercise = (function () {
  "use strict";

  let pyodideReady = null;        // Promise<Pyodide> | null
  let pyodideAvailable = null;   // tri-state while probing

  // ---------------------------------------------------------------------------
  // Pyodide loader
  // ---------------------------------------------------------------------------
  function loadPyodideAsync() {
    if (pyodideReady) return pyodideReady;

    pyodideAvailable = false;
    // Vendored per plan §4 — see static/vendor/pyodide/README.md
    const scriptUrl = "/static/vendor/pyodide/pyodide.js";

    pyodideReady = new Promise((resolve, reject) => {
      const probe = new XMLHttpRequest();
      probe.open("HEAD", scriptUrl, true);
      probe.onload = function () {
        if (probe.status >= 200 && probe.status < 400) {
          const s = document.createElement("script");
          s.src = scriptUrl;
          s.onload = async function () {
            try {
              /* global loadPyodide */
              const py = await loadPyodide({
                indexURL: "/static/vendor/pyodide/",
              });
              pyodideAvailable = true;
              resolve(py);
            } catch (err) {
              console.warn("Pyodide init failed:", err);
              pyodideAvailable = false;
              reject(err);
            }
          };
          s.onerror = function () { reject(new Error("pyodide.js load error")); };
          document.head.appendChild(s);
        } else {
          reject(new Error("Pyodide not vendored at " + scriptUrl));
        }
      };
      probe.onerror = function () { reject(new Error("Pyodide probe failed")); };
      probe.send();
    });

    // Cache: failed loads should retry, but we keep the rejected promise so
    // the next runner call sees the failure cleanly.
    pyodideReady.catch(() => { pyodideReady = null; });
    return pyodideReady;
  }

  /**
   * Run Python code. Returns {stdout, stderr, result} on resolve.
   * Promise rejects when Pyodide cannot be loaded.
   */
  function runPython(code) {
    return loadPyodideAsync().then(function (py) {
      let stdout = "", stderr = "";
      py.setStdout({ batched: (s) => { stdout += s; } });
      py.setStderr({ batched: (s) => { stderr += s; } });
      let result = null;
      try {
        result = py.runPython(code || "");
      } catch (err) {
        stderr += "\n" + (err && err.message ? err.message : String(err));
      }
      return { stdout: stdout, stderr: stderr, result: result };
    });
  }

  // ---------------------------------------------------------------------------
  // Generic JavaScript sandbox runner (code_js) — runs in a sandboxed iframe.
  // ---------------------------------------------------------------------------
  function runJsInSandbox(code, onResult) {
    const iframe = document.createElement("iframe");
    iframe.setAttribute("sandbox", "allow-scripts");
    iframe.style.display = "none";
    document.body.appendChild(iframe);
    const win = iframe.contentWindow;
    const onMessage = (ev) => {
      if (ev.source !== win) return;
      onResult(ev.data || {});
      window.removeEventListener("message", onMessage);
      setTimeout(() => { if (iframe.parentNode) iframe.parentNode.removeChild(iframe); }, 10);
    };
    window.addEventListener("message", onMessage);
    const doc = iframe.contentDocument || iframe.contentWindow.document;
    doc.open();
    doc.write(
      "<html><body><script>" +
      "try {\n" +
      "  var __out = '';\n" +
      "  var console = { log: function(){ __out += Array.prototype.join.call(arguments,' ') + '\\n'; } };\n" +
      "  (function(){\n" + code + "\n})();\n" +
      "  parent.postMessage({ stdout: __out, stderr: '', ok: true }, '*');\n" +
      "} catch (e) { parent.postMessage({ stdout: '', stderr: String(e), ok: false }, '*'); }\n" +
      "</" + "script></body></html>"
    );
    doc.close();
  }

  // ---------------------------------------------------------------------------
  // code_py grading: run student code + unit-test spec, return pass/fail.
  // ---------------------------------------------------------------------------
  function gradeCodePy(spec, code) {
    return runPython(code).then(async function (out) {
      if (!spec.tests || !spec.tests.length) {
        return { passed: true, stdout: out.stdout, stderr: out.stderr };
      }
      // Tests are authored as Python expressions that must evaluate truthy.
      const py = await loadPyodideAsync();
      const results = [];
      for (const t of spec.tests) {
        try {
          const v = py.runPython(t.expr);
          results.push({ name: t.name || t.expr, passed: !!v });
        } catch (e) {
          results.push({ name: t.name || t.expr, passed: false, error: String(e) });
        }
      }
      const allPass = results.every((r) => r.passed);
      return { passed: allPass, stdout: out.stdout, stderr: out.stderr, results: results };
    });
  }

  // ---------------------------------------------------------------------------
  // Helpers for the per-kind widgets
  // ---------------------------------------------------------------------------
  function compareCaseInsensitive(a, b) {
    return (a || "").trim().toLowerCase() === (b || "").trim().toLowerCase();
  }

  function checkRegex(pattern, flags, samples) {
    // samples: [{ input, shouldMatch }]
    let re;
    try { re = new RegExp(pattern, flags || ""); }
    catch (e) { return { passed: false, error: "invalid regex: " + e }; }
    const results = samples.map((s) => ({ input: s.input,
      matched: re.test(s.input) === !!s.shouldMatch }));
    return { passed: results.every((r) => r.matched), results: results };
  }

  // Pack the exposed surface
  return {
    runPython: runPython,
    runJs:     runJsInSandbox,
    gradeCodePy: gradeCodePy,
    checkRegex:  checkRegex,
    equalsIgnoreCase: compareCaseInsensitive,
    isPyodideAvailable: () => pyodideAvailable === true,
  };
})();
