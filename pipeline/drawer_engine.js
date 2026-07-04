/* ============================================================
   Gorgias — Citation Drawer (B1)
   window.DrawerEngine.render(el, node, scenario) per A1's DRAWER-MOUNT contract.
   Shows: cite header, verbatim excerpt with the operative clause <mark>-highlighted,
   source URL, Vulcan corpus tag, and a MODELED badge where applicable.
   ============================================================ */
window.DrawerEngine = (function () {
  "use strict";
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function fmtLong(v) {
    if (v == null) return "—";
    return (v < 0 ? "−" : "") + "$" + Math.abs(Math.round(v)).toLocaleString("en-US");
  }
  function corpusTag(node) {
    return node.corpus_tag || (node.type === "budget"
      ? "Public Finance Records · 26.6B records" : "State Statutes");
  }
  function markHtml(text, mark) {
    var t = esc(text);
    if (mark) {
      var m = esc(mark), i = t.indexOf(m);
      if (i >= 0) t = t.slice(0, i) + '<mark class="dr-mark">' + m + '</mark>' + t.slice(i + m.length);
    }
    // preserve statute paragraph breaks
    return t.replace(/\n/g, "<br>");
  }
  function badge(label, kind) {
    return '<span class="dr-badge ' + (kind || "") + '">' + esc(label) + "</span>";
  }
  function childAgency(node, scenario) {
    var kids = scenario.nodes.filter(function (n) { return n.parent === node.id; });
    for (var i = 0; i < kids.length; i++) if (kids[i].type === "agency") return kids[i];
    return scenario.nodes.find(function (n) { return n.type === "agency"; });
  }

  function renderBudget(node) {
    var h = '<div class="dr-fiscalrow">';
    if (node.actual_2025_usd != null) {
      h += '<div class="dr-fcell"><div class="dr-flabel">actual (2025 LBB)</div>' +
           '<div class="dr-fval">' + fmtLong(node.actual_2025_usd) + "</div></div>";
      h += '<div class="dr-farrow">×' + (node.scale_factor || 1.5) + "</div>";
    }
    h += '<div class="dr-fcell dr-fcell-hero"><div class="dr-flabel">modeled projection · $200k</div>' +
         '<div class="dr-fval dr-fval-hero">' + fmtLong(node.delta_usd) + "</div></div></div>";
    if (node.excerpt) h += '<blockquote class="dr-quote">' + esc(node.excerpt) + "</blockquote>";
    if (node.actual_2025_line)
      h += '<div class="dr-kv"><span>2025 LBB line</span><b>' + esc(node.actual_2025_line) + "</b></div>";
    return h;
  }

  function render(el, node, scenario) {
    if (!node) { el.innerHTML = ""; return; }
    var modeled = !!node.modeled, verbatim = node.verbatim === true, tag = corpusTag(node);
    var html = '<div class="dr-title">' + esc(node.label) + "</div>";

    var isAgency = node.type === "agency";

    var chips = '<div class="dr-chiprow">';
    var chipCite = isAgency ? (node.authority_cite || node.cite) : node.cite;
    if (chipCite) chips += '<span class="chip"><span class="anchor"></span>' + esc(chipCite) + "</span>";
    chips += '<span class="dr-corpus">' + esc(tag) + "</span>";
    if (modeled) chips += badge("MODELED", "modeled");
    if (isAgency) chips += badge(node.t5_validated ? "GLM-VALIDATED" : "ANALYSIS", node.t5_validated ? "t5" : "sev");
    if (node.type === "conflict") chips += badge("SEVERITY " + (node.severity || 0), "sev");
    html += chips + "</div>";

    // provenance: agencies are analytical (authority chain), never "retrieved verbatim"
    var prov;
    if (isAgency) {
      prov = "ANALYSIS · Vulcan corpus · " + tag + " · " + esc(node.authority_cite || node.cite || "authority") +
        (node.t5_validated ? " · GLM-validated" : " · modeled analysis");
    } else {
      prov = "SOURCE · Vulcan corpus · " + tag + " · " + (node.cite || "modeled") +
        (modeled ? " · MODELED" : (verbatim ? " · retrieved verbatim" : ""));
    }
    html += '<div class="dr-prov">' + esc(prov) + "</div>";

    if (node.type === "budget") {
      html += renderBudget(node);
    } else if (isAgency) {
      // analytical treatment — no highlighted quote; authority + action + approval-gate holder
      if (node.action_required) {
        html += '<div class="dr-blocklabel">ACTION REQUIRED</div>';
        html += '<div class="dr-rationale">' + esc(node.action_required) + "</div>";
      }
      html += '<div class="dr-kv"><span>Authority</span><b>' + esc(node.authority_cite || node.cite || "—") + "</b></div>";
      html += '<div class="dr-kv"><span>Approval gate</span><b>' + esc(node.approval_gate || "—") + "</b></div>";
      if (node.deadline_cite) html += '<div class="dr-kv"><span>Deadline</span><b>' + esc(node.deadline_cite) + "</b></div>";
      if (node.clock_days) html += '<div class="dr-kv"><span>Est. clock</span><b>' + node.clock_days + " days</b></div>";
    } else {
      if (node.excerpt) {
        var lbl = node.type === "conflict" ? "GROUNDING · operative source"
          : (node.heading ? esc(node.heading) : "VERBATIM SOURCE");
        html += '<div class="dr-blocklabel">' + lbl + "</div>";
        html += '<blockquote class="dr-quote">' + markHtml(node.excerpt, node.mark) + "</blockquote>";
      }
      if (node.type === "conflict" && node.rationale) {
        html += '<div class="dr-blocklabel">GROUNDING · why it collides</div>';
        html += '<div class="dr-rationale">' + esc(node.rationale) + "</div>";
      }
    }

    // source URL only for verbatim-sourced nodes; agencies are analytical (no scraped source line)
    if (node.source_url) {
      html += '<div class="dr-srclabel">SOURCE URL</div>';
      html += '<a class="dr-url" href="' + esc(node.source_url) + '" target="_blank" rel="noopener">' +
        esc(node.source_url) + "</a>";
    } else if (modeled && !isAgency) {
      html += '<div class="dr-url dr-url-modeled">No scraped source — modeled dependency</div>';
    }
    if (node.fetched_at)
      html += '<div class="dr-fetched">retrieved ' + esc(String(node.fetched_at).slice(0, 10)) + "</div>";

    if (node.type !== "agency") {
      var ag = childAgency(node, scenario);
      if (ag) {
        html += '<div class="dr-next"><div class="dr-nextlabel">NEXT STEP · human gate</div>' +
          '<div class="dr-nextbody">' + esc(ag.label) +
          (ag.approval_gate ? " · <b>" + esc(ag.approval_gate) + "</b>" : "") +
          (ag.clock_days ? " · " + ag.clock_days + "d" : "") + "</div></div>";
      }
    }
    el.innerHTML = html;
  }

  return { render: render };
})();
