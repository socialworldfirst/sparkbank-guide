"""Build the SparkBank Guide site as a single password-gated HTML file.
Pattern: PBKDF2 + AES-GCM, password 'claude'. Same as Notebook.
"""
import base64
import json
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes

PASSWORD = "nerds"
ITERATIONS = 100_000

# ---------- Content ----------
# Sections are markdown-lite HTML. The renderer just inserts them into the page.

CONTENT = {
    "tagline": "Your content angle machine. Mine your own work for what's worth posting.",
    "summary_one_liner": "SparkBank scans your Claude sessions for hidden content angles, banks them, and turns the best ones into production-ready briefs.",
    "sections": [
        {
            "id": "how-it-works",
            "title": "How it works",
            "kind": "flow",
            "body": """
                <p class="lead">Three loops. You only touch one.</p>
                <div class="flow">
                    <div class="flow-row">
                        <div class="flow-step">
                            <div class="flow-num">1</div>
                            <div class="flow-label">Scan</div>
                            <div class="flow-desc">Reads your inbox + handoffs. Extracts non-obvious angles. Filters for privacy. Scores against your audience profile.</div>
                            <div class="flow-actor">Auto / on-demand</div>
                        </div>
                        <div class="flow-arrow">&rarr;</div>
                        <div class="flow-step">
                            <div class="flow-num">2</div>
                            <div class="flow-label">Bank</div>
                            <div class="flow-desc">Top sparks land in Spark_Bank.xlsx on Drive. Status flow: raw &rarr; sharpened &rarr; greenlit &rarr; in production &rarr; shipped.</div>
                            <div class="flow-actor">Spreadsheet on Drive</div>
                        </div>
                        <div class="flow-arrow">&rarr;</div>
                        <div class="flow-step you">
                            <div class="flow-num">3</div>
                            <div class="flow-label">Greenlight</div>
                            <div class="flow-desc">You pick one. Run the angle finder to sharpen. Spawn a production handoff. Ship.</div>
                            <div class="flow-actor">You. ~10 min/week.</div>
                        </div>
                    </div>
                </div>
                <p class="note">Loops 1 and 2 happen without you. Loop 3 is your only decision moment.</p>
            """
        },
        {
            "id": "drop",
            "title": "What you can drop to me",
            "kind": "drop",
            "body": """
                <p class="lead">Drop it in any session, any time. The next scan picks it up. No skill invocation needed.</p>
                <div class="drop-grid">
                    <div class="drop-card">
                        <div class="drop-icon">[1]</div>
                        <h3>Meeting notes</h3>
                        <p>Transcripts, recap docs, voice memo summaries from internal meetings. Steven's audio recordings via "drop the .txt".</p>
                        <div class="drop-example">"Here's the transcript from today's CSN alignment meeting"</div>
                    </div>
                    <div class="drop-card">
                        <div class="drop-icon">[2]</div>
                        <h3>Links</h3>
                        <p>Tweets, articles, LinkedIn posts, competitor moves, blog posts that caught your eye.</p>
                        <div class="drop-example">"Check this out: [URL] — what's the angle here?"</div>
                    </div>
                    <div class="drop-card">
                        <div class="drop-icon">[3]</div>
                        <h3>Random observations</h3>
                        <p>"I noticed X in our data." "Our supplier did Y today." "Megan said Z in slack." One-line drops.</p>
                        <div class="drop-example">"Suppliers keep asking us to skip Trade Assurance now"</div>
                    </div>
                    <div class="drop-card">
                        <div class="drop-icon">[4]</div>
                        <h3>Data points</h3>
                        <p>Numbers from Sprout, Meta Ads, YouTube Studio, customer calls, financial reports. Real numbers from real sources.</p>
                        <div class="drop-example">"LinkedIn drove 1,025 of 1,028 link clicks last month"</div>
                    </div>
                    <div class="drop-card">
                        <div class="drop-icon">[5]</div>
                        <h3>Behind-the-scenes</h3>
                        <p>Operational decisions, tool choices, things you cut, things you tried and abandoned, why you changed your mind.</p>
                        <div class="drop-example">"We dropped 4 SaaS tools and the system got better"</div>
                    </div>
                    <div class="drop-card">
                        <div class="drop-icon">[6]</div>
                        <h3>Customer voice</h3>
                        <p>Real things real importers say. Voice notes, slack threads, support tickets, sales call recaps.</p>
                        <div class="drop-example">"A customer told me USD wires were freezing them last quarter"</div>
                    </div>
                    <div class="drop-card">
                        <div class="drop-icon">[7]</div>
                        <h3>Screenshots</h3>
                        <p>UI screenshots, dashboard charts, social media posts, memes, anything visual that triggered a thought.</p>
                        <div class="drop-example">"What's the spark in this screenshot?" + image</div>
                    </div>
                    <div class="drop-card">
                        <div class="drop-icon">[8]</div>
                        <h3>Half-formed thoughts</h3>
                        <p>Drafts, abandoned posts, fragmentary ideas, "I had this thought but didn't finish it." The scanner can complete the shape.</p>
                        <div class="drop-example">"I want to write something about Y but don't know the angle"</div>
                    </div>
                </div>
                <div class="callout">
                    <strong>Privacy filter:</strong> KOL contracts, Meta Ads spend, Ant Group internal strategy, and personnel transitions are auto-filtered. You can drop them; they'll be flagged as filtered, not banked.
                </div>
            """
        },
        {
            "id": "kickoff",
            "title": "Kickoff phrases — what to say",
            "kind": "kickoff",
            "body": """
                <p class="lead">Trigger the right step with these phrases. No skill memorisation required.</p>
                <div class="phrase-list">
                    <div class="phrase">
                        <div class="phrase-trigger">"Scan for sparks"</div>
                        <div class="phrase-desc">Or "find content angles in my work" or "what content sparks did I miss". Runs <code>/spark_scan</code>.</div>
                    </div>
                    <div class="phrase">
                        <div class="phrase-trigger">"Show me the spark bank"</div>
                        <div class="phrase-desc">Or "what's in the bank" or "what's queued". Pulls latest from Drive, shows filterable view. Runs <code>/content_bank</code>.</div>
                    </div>
                    <div class="phrase">
                        <div class="phrase-trigger">"Sharpen S012"</div>
                        <div class="phrase-desc">Or "let's sharpen the trench coat one". Picks a spark, runs the angle finder, drops a Google Doc brief.</div>
                    </div>
                    <div class="phrase">
                        <div class="phrase-trigger">"Give me a deep post on X"</div>
                        <div class="phrase-desc">Skips the bank, runs the angle finder fresh on a topic. Useful when you want a single deep post without scanning.</div>
                    </div>
                    <div class="phrase">
                        <div class="phrase-trigger">"Push S012 to production"</div>
                        <div class="phrase-desc">Or "let's make this one". Spawns a handoff doc. Fresh session takes the brief into YT script + reels.</div>
                    </div>
                    <div class="phrase">
                        <div class="phrase-trigger">"Archive S012"</div>
                        <div class="phrase-desc">Or "skip this one" or "not feeling that one". Moves to archive sheet, gone from view.</div>
                    </div>
                    <div class="phrase">
                        <div class="phrase-trigger">"What's the angle here?" + drop content</div>
                        <div class="phrase-desc">Drop a link, screenshot, or note. Runs <code>/wf_spark</code> for a quick read, or <code>/spark_scan</code> if it warrants banking.</div>
                    </div>
                </div>
            """
        },
        {
            "id": "recipes",
            "title": "Recipes",
            "kind": "recipes",
            "body": """
                <p class="lead">Three workflows you'll actually use.</p>
                <div class="recipes">

                    <div class="recipe">
                        <div class="recipe-num">A</div>
                        <h3>End-of-day spark capture</h3>
                        <p class="recipe-when"><strong>When:</strong> after a substantive session (KOL strategy, distribution build, customer call recap)</p>
                        <ol>
                            <li>Tell me <em>"scan for sparks"</em></li>
                            <li>I read inbox + handoffs from today, extract candidates, score them, append the top 4 to the bank</li>
                            <li>I show you the new sparks in chat (one line each)</li>
                            <li>You ignore or note "ooh that one" for later</li>
                        </ol>
                        <div class="recipe-time">Total: 3-5 min</div>
                    </div>

                    <div class="recipe">
                        <div class="recipe-num">B</div>
                        <h3>Weekly greenlight</h3>
                        <p class="recipe-when"><strong>When:</strong> Monday or Sunday morning, ~10 min</p>
                        <ol>
                            <li>Tell me <em>"show me the spark bank"</em></li>
                            <li>I pull latest, show top 5-10 raw sparks ranked by score</li>
                            <li>You pick 1-2 you want to make</li>
                            <li>Tell me <em>"sharpen S0XX"</em> for each</li>
                            <li>I run the angle finder, drop Google Doc briefs</li>
                            <li>Tell me <em>"push S0XX to production"</em></li>
                            <li>I spawn handoffs. Production sessions build the YT + shorts.</li>
                        </ol>
                        <div class="recipe-time">Total: 10-15 min, then production runs in background</div>
                    </div>

                    <div class="recipe">
                        <div class="recipe-num">C</div>
                        <h3>Drop and forget</h3>
                        <p class="recipe-when"><strong>When:</strong> mid-day, you read something interesting</p>
                        <ol>
                            <li>Drop the link / quote / screenshot in any session</li>
                            <li>Don't say anything special. Just drop it.</li>
                            <li>Next <em>"scan for sparks"</em> picks it up automatically</li>
                            <li>If it's a great spark, it surfaces in the next weekly greenlight</li>
                            <li>If it's noise, it gets filtered and you never see it again</li>
                        </ol>
                        <div class="recipe-time">Total: 5 seconds. Zero friction.</div>
                    </div>

                </div>
            """
        },
        {
            "id": "cadence",
            "title": "Cadence",
            "kind": "cadence",
            "body": """
                <p class="lead">No fixed schedule. Three rhythms that work.</p>
                <table class="cadence-table">
                    <thead>
                        <tr><th>Rhythm</th><th>What you do</th><th>Output</th><th>Risk</th></tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Reactive</strong><br><span class="muted">Whenever</span></td>
                            <td>Drop content into any session. Run <code>/spark_scan</code> when you remember.</td>
                            <td>Bank slowly accumulates. You greenlight when something looks ready.</td>
                            <td>Stuff gets missed if you forget to scan.</td>
                        </tr>
                        <tr>
                            <td><strong>Weekly</strong><br><span class="muted">Sun or Mon AM</span></td>
                            <td>One ~10 min check. View bank, sharpen 1-2, push to production.</td>
                            <td>1-2 pieces of content shipped per week. Steady cadence.</td>
                            <td>Bank can fill up if production capacity lags.</td>
                        </tr>
                        <tr>
                            <td><strong>Automated</strong><br><span class="muted">v1, deferred</span></td>
                            <td>Daily 9pm scan runs by itself. Sunday 8am sharpen runs by itself. You only see weekly inbox digest.</td>
                            <td>Hands-off. Briefs ready every Monday morning.</td>
                            <td>Quality of judge prompt determines whether output is signal or noise.</td>
                        </tr>
                    </tbody>
                </table>
                <p class="note"><strong>Recommendation:</strong> Reactive + weekly. Skip automated until you've used it for a month and the rubric is tuned.</p>
            """
        },
        {
            "id": "files",
            "title": "Where things live",
            "kind": "files",
            "body": """
                <div class="files-grid">
                    <div class="file-card">
                        <h4>The bank</h4>
                        <code>gdrive:Spark Bank/Spark_Bank.xlsx</code>
                        <p><a href="https://drive.google.com/open?id=1A_t0lmBpJxEoql8rKJsdC64k3EN_3t5E" target="_blank">Open in Drive &rarr;</a></p>
                        <p class="muted">4 sheets: Sparks (active), Archive, Scan_Log, Schema</p>
                    </div>
                    <div class="file-card">
                        <h4>Sharpened briefs</h4>
                        <code>gdrive:Content Drafts/Angle Finder/</code>
                        <p class="muted">Each greenlit spark gets a Google Doc here</p>
                    </div>
                    <div class="file-card">
                        <h4>Production handoffs</h4>
                        <code>~/Documents/Claude/Handoffs/</code>
                        <p class="muted">Per-spark folders for production sessions to load</p>
                    </div>
                    <div class="file-card">
                        <h4>Privacy filter</h4>
                        <code>~/Documents/Claude/SparkBank/privacy_filter.yaml</code>
                        <p class="muted">Edit to add/remove exclusions. Re-read on every scan.</p>
                    </div>
                    <div class="file-card">
                        <h4>Audience profiles</h4>
                        <code>~/Documents/Claude/SparkBank/audience_profiles/</code>
                        <p class="muted">Operator Importer is live. Cross-Border Seller in v1.</p>
                    </div>
                    <div class="file-card">
                        <h4>The scan engine</h4>
                        <code>~/.claude/skills/spark_scan/SKILL.md</code>
                        <p class="muted">Edit to change the scoring rubric or scope</p>
                    </div>
                </div>
            """
        },
        {
            "id": "examples",
            "title": "Real sparks already in your bank",
            "kind": "examples",
            "body": """
                <p class="lead">From today's first live scan. These were extracted from your inbox + handoffs without you doing anything.</p>
                <div class="example-list">
                    <div class="example">
                        <div class="example-head">
                            <span class="example-id">S001</span>
                            <span class="example-score">92/100</span>
                        </div>
                        <h3>Trade Assurance is three products in one trench coat. Unbundle them.</h3>
                        <p class="example-source">From: Trade Assurance Unbundled session</p>
                        <p class="example-why">Reframes the most-debated payment decision in the WF audience. Names the bundle nobody else has named. Already proven as a LinkedIn longform draft.</p>
                    </div>
                    <div class="example">
                        <div class="example-head">
                            <span class="example-id">S002</span>
                            <span class="example-score">78/100</span>
                        </div>
                        <h3>LinkedIn punches 9x above platform average for B2B fintech.</h3>
                        <p class="example-source">From: Sprout Social pull (your own data)</p>
                        <p class="example-why">94 eng/post vs 10 platform avg. 1,025 of 1,028 link clicks come from LinkedIn. Hard data-backed counter to "spread evenly across channels" instinct.</p>
                    </div>
                    <div class="example">
                        <div class="example-head">
                            <span class="example-id">S003</span>
                            <span class="example-score">70/100</span>
                        </div>
                        <h3>How we mined a 62-min raw factory tour into a complete YouTube package.</h3>
                        <p class="example-source">From: Made in England Sourced in China YouTube metadata session</p>
                        <p class="example-why">1806 transcript segments, full SEO package generated, 10 chapter timestamps mapped to actual segment times. Behind-the-scenes process content.</p>
                    </div>
                    <div class="example">
                        <div class="example-head">
                            <span class="example-id">S004</span>
                            <span class="example-score">72/100</span>
                        </div>
                        <h3>Why we built a calendar.xlsx instead of a SaaS scheduler.</h3>
                        <p class="example-source">From: Distribution Architecture Phase 1 build</p>
                        <p class="example-why">Counter-case to "use a tool" default. 278 rows tracking full status flow, daily auto-pull, three skills wired. Ops wisdom for solo content leads.</p>
                    </div>
                </div>
                <p class="note"><strong>Note:</strong> 1 spark was filtered for privacy (touched the "Claude Max plan" exclusion keyword). The system is working as designed.</p>
            """
        }
    ]
}

# ---------- Encrypt ----------

salt = os.urandom(16)
iv = os.urandom(12)

kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=ITERATIONS,
)
key = kdf.derive(PASSWORD.encode("utf-8"))
aesgcm = AESGCM(key)
plaintext = json.dumps(CONTENT, ensure_ascii=False).encode("utf-8")
ciphertext = aesgcm.encrypt(iv, plaintext, None)

blob = {
    "v": 1,
    "salt": base64.b64encode(salt).decode("ascii"),
    "iv": base64.b64encode(iv).decode("ascii"),
    "iterations": ITERATIONS,
    "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
}

# ---------- HTML ----------

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SparkBank Guide</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; }
:root {
  --pink: #FF0051;
  --pink-soft: #FFE5EE;
  --navy: #0A1F44;
  --navy-soft: #2B3F6B;
  --cream: #FBF7F2;
  --paper: #FFFFFF;
  --ink: #1A1A1A;
  --muted: #6B7280;
  --line: #E5E7EB;
}
html, body { margin: 0; padding: 0; }
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  color: var(--ink);
  background: var(--cream);
  -webkit-font-smoothing: antialiased;
}
code { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 0.9em; background: var(--cream); padding: 2px 6px; border-radius: 4px; color: var(--navy); }
a { color: var(--pink); text-decoration: none; border-bottom: 1px solid transparent; transition: border-color 0.15s; }
a:hover { border-bottom-color: var(--pink); }

/* ---- Login overlay ---- */
.login {
  position: fixed; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--cream); z-index: 100;
}
.login-card {
  background: var(--paper);
  padding: 48px 40px;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(10, 31, 68, 0.06);
  width: 360px; max-width: 90vw;
  text-align: center;
}
.login-mark { font-family: 'Fraunces', serif; font-style: italic; font-size: 14px; color: var(--pink); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 16px; }
.login h1 { font-family: 'Fraunces', serif; font-weight: 500; font-size: 28px; margin: 0 0 8px; color: var(--navy); }
.login p { color: var(--muted); margin: 0 0 24px; font-size: 14px; }
.login input {
  width: 100%; padding: 12px 16px; font-size: 16px;
  border: 1px solid var(--line); border-radius: 6px;
  background: var(--paper); color: var(--ink);
  font-family: inherit;
}
.login input:focus { outline: 2px solid var(--pink); outline-offset: -1px; border-color: var(--pink); }
.login button {
  width: 100%; padding: 12px 16px; margin-top: 12px;
  background: var(--pink); color: var(--paper);
  border: none; border-radius: 6px; font-size: 15px; font-weight: 600;
  font-family: inherit; cursor: pointer;
  transition: background 0.15s;
}
.login button:hover { background: #d80045; }
.login-error { color: var(--pink); font-size: 13px; margin-top: 12px; min-height: 18px; }

/* ---- App layout ---- */
.app { display: none; }
.app.active { display: block; }

.container { max-width: 880px; margin: 0 auto; padding: 60px 32px 100px; }

header.hero {
  text-align: left;
  padding-bottom: 48px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 56px;
}
.hero-mark { font-family: 'Fraunces', serif; font-style: italic; font-size: 13px; color: var(--pink); letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 12px; }
.hero h1 { font-family: 'Fraunces', serif; font-weight: 500; font-size: 56px; line-height: 1.05; letter-spacing: -0.02em; margin: 0 0 16px; color: var(--navy); }
.hero h1 em { font-style: italic; color: var(--pink); }
.hero-tag { font-size: 19px; line-height: 1.5; color: var(--muted); margin: 0 0 20px; max-width: 620px; }
.hero-summary { font-size: 16px; line-height: 1.6; color: var(--ink); max-width: 620px; }

/* ---- Sections ---- */
section { margin-bottom: 80px; }
section h2 { font-family: 'Fraunces', serif; font-weight: 500; font-size: 36px; line-height: 1.1; letter-spacing: -0.01em; margin: 0 0 8px; color: var(--navy); }
section .sec-id { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--pink); text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 20px; }
.lead { font-size: 18px; line-height: 1.55; color: var(--navy-soft); margin: 0 0 32px; max-width: 640px; }

/* ---- Flow diagram ---- */
.flow { background: var(--paper); border-radius: 12px; padding: 32px; box-shadow: 0 1px 3px rgba(10,31,68,0.04); }
.flow-row { display: grid; grid-template-columns: 1fr auto 1fr auto 1fr; gap: 16px; align-items: stretch; }
.flow-step { padding: 20px; background: var(--cream); border-radius: 8px; border: 1px solid var(--line); }
.flow-step.you { background: var(--pink-soft); border-color: var(--pink); }
.flow-num { font-family: 'Fraunces', serif; font-style: italic; font-size: 36px; color: var(--pink); line-height: 1; margin-bottom: 8px; }
.flow-label { font-weight: 600; font-size: 16px; color: var(--navy); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
.flow-desc { font-size: 14px; line-height: 1.5; color: var(--ink); margin-bottom: 12px; }
.flow-actor { font-family: 'Fraunces', serif; font-style: italic; font-size: 13px; color: var(--muted); }
.flow-arrow { display: flex; align-items: center; justify-content: center; font-size: 24px; color: var(--pink); font-weight: 300; }
.note { font-family: 'Fraunces', serif; font-style: italic; font-size: 16px; color: var(--navy-soft); margin-top: 24px; }

/* ---- Drop grid ---- */
.drop-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
.drop-card { background: var(--paper); border-radius: 10px; padding: 24px; border: 1px solid var(--line); transition: transform 0.15s, box-shadow 0.15s; }
.drop-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(10,31,68,0.08); }
.drop-icon { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--pink); margin-bottom: 12px; font-weight: 600; }
.drop-card h3 { font-family: 'Fraunces', serif; font-weight: 500; font-size: 22px; margin: 0 0 10px; color: var(--navy); }
.drop-card p { font-size: 14px; line-height: 1.5; color: var(--ink); margin: 0 0 14px; }
.drop-example { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--navy-soft); background: var(--cream); padding: 10px 12px; border-radius: 6px; border-left: 3px solid var(--pink); }
.callout { margin-top: 32px; padding: 20px 24px; background: var(--paper); border-left: 4px solid var(--pink); border-radius: 6px; font-size: 15px; line-height: 1.6; }
.callout strong { color: var(--pink); }

/* ---- Phrase list ---- */
.phrase-list { display: flex; flex-direction: column; gap: 12px; }
.phrase { background: var(--paper); padding: 20px 24px; border-radius: 10px; border: 1px solid var(--line); }
.phrase-trigger { font-family: 'Fraunces', serif; font-style: italic; font-size: 22px; color: var(--pink); margin-bottom: 8px; }
.phrase-desc { font-size: 14px; line-height: 1.55; color: var(--ink); }
.phrase-desc code { background: var(--cream); }

/* ---- Recipes ---- */
.recipes { display: flex; flex-direction: column; gap: 20px; }
.recipe { background: var(--paper); padding: 32px; border-radius: 12px; border: 1px solid var(--line); position: relative; }
.recipe-num { position: absolute; top: 24px; right: 24px; font-family: 'Fraunces', serif; font-style: italic; font-size: 56px; color: var(--pink); line-height: 1; opacity: 0.25; }
.recipe h3 { font-family: 'Fraunces', serif; font-weight: 500; font-size: 26px; margin: 0 0 8px; color: var(--navy); padding-right: 60px; }
.recipe-when { font-size: 14px; color: var(--muted); margin: 0 0 16px; }
.recipe ol { margin: 0 0 16px; padding-left: 20px; }
.recipe ol li { font-size: 15px; line-height: 1.7; color: var(--ink); margin-bottom: 4px; }
.recipe ol li em { color: var(--pink); font-style: italic; }
.recipe-time { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--navy-soft); background: var(--cream); padding: 6px 10px; border-radius: 4px; display: inline-block; }

/* ---- Cadence table ---- */
.cadence-table { width: 100%; border-collapse: collapse; background: var(--paper); border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(10,31,68,0.04); }
.cadence-table th { background: var(--navy); color: var(--paper); text-align: left; padding: 14px 18px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
.cadence-table td { padding: 18px; border-top: 1px solid var(--line); font-size: 14px; line-height: 1.5; vertical-align: top; }
.cadence-table td:first-child { width: 18%; }
.cadence-table strong { color: var(--navy); }
.cadence-table code { background: var(--cream); }
.muted { color: var(--muted); font-size: 12px; font-family: 'JetBrains Mono', monospace; }

/* ---- Files ---- */
.files-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
.file-card { background: var(--paper); padding: 20px 24px; border-radius: 10px; border: 1px solid var(--line); }
.file-card h4 { font-family: 'Fraunces', serif; font-weight: 500; font-size: 19px; margin: 0 0 10px; color: var(--navy); }
.file-card code { display: block; word-break: break-all; background: var(--cream); padding: 8px 10px; border-radius: 4px; font-size: 12px; margin-bottom: 8px; }
.file-card p { font-size: 13px; margin: 6px 0 0; }

/* ---- Examples ---- */
.example-list { display: flex; flex-direction: column; gap: 16px; }
.example { background: var(--paper); padding: 24px 28px; border-radius: 10px; border: 1px solid var(--line); border-left: 4px solid var(--pink); }
.example-head { display: flex; gap: 12px; align-items: baseline; margin-bottom: 8px; }
.example-id { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--pink); font-weight: 600; }
.example-score { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--navy-soft); }
.example h3 { font-family: 'Fraunces', serif; font-weight: 500; font-size: 22px; line-height: 1.3; margin: 0 0 10px; color: var(--navy); }
.example-source { font-size: 12px; color: var(--muted); margin: 0 0 10px; font-family: 'JetBrains Mono', monospace; }
.example-why { font-size: 14px; line-height: 1.55; color: var(--ink); margin: 0; }

/* ---- Footer ---- */
footer.foot { margin-top: 80px; padding-top: 32px; border-top: 1px solid var(--line); font-size: 12px; color: var(--muted); font-family: 'JetBrains Mono', monospace; text-align: center; }

/* ---- Responsive ---- */
@media (max-width: 720px) {
  .container { padding: 40px 20px 60px; }
  .hero h1 { font-size: 40px; }
  section h2 { font-size: 28px; }
  .flow-row { grid-template-columns: 1fr; }
  .flow-arrow { transform: rotate(90deg); margin: 8px 0; }
  .recipe-num { font-size: 36px; top: 16px; right: 16px; }
  .recipe h3 { padding-right: 50px; }
  .cadence-table { font-size: 13px; }
  .cadence-table th, .cadence-table td { padding: 12px; }
}
</style>
</head>
<body>

<div class="login" id="login">
  <div class="login-card">
    <div class="login-mark">SparkBank</div>
    <h1>Steven's guide</h1>
    <p>Password to unlock</p>
    <form id="loginForm">
      <input type="password" id="pw" autocomplete="current-password" autofocus>
      <button type="submit">Unlock</button>
      <div class="login-error" id="loginError"></div>
    </form>
  </div>
</div>

<div class="app" id="app">
  <div class="container">
    <header class="hero">
      <div class="hero-mark">SparkBank Guide</div>
      <h1>Your <em>content angle</em> machine.</h1>
      <p class="hero-tag" id="tagline"></p>
      <p class="hero-summary" id="summary"></p>
    </header>
    <main id="content"></main>
    <footer class="foot">
      Built for Steven. Update content via <code>~/Documents/Claude/sparkbank-guide/build.py</code>, then push.
    </footer>
  </div>
</div>

<script>
const BLOB = __BLOB__;

function b64ToBytes(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

async function deriveKey(password, salt, iterations) {
  const enc = new TextEncoder();
  const baseKey = await crypto.subtle.importKey(
    "raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]
  );
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations, hash: "SHA-256" },
    baseKey,
    { name: "AES-GCM", length: 256 },
    false, ["decrypt"]
  );
}

async function decrypt(password) {
  const salt = b64ToBytes(BLOB.salt);
  const iv = b64ToBytes(BLOB.iv);
  const ct = b64ToBytes(BLOB.ciphertext);
  const key = await deriveKey(password, salt, BLOB.iterations);
  const plaintext = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, key, ct);
  return JSON.parse(new TextDecoder().decode(plaintext));
}

function render(content) {
  document.getElementById("tagline").textContent = content.tagline;
  document.getElementById("summary").textContent = content.summary_one_liner;
  const main = document.getElementById("content");
  main.innerHTML = content.sections.map(s => `
    <section id="${s.id}">
      <div class="sec-id">${s.id}</div>
      <h2>${s.title}</h2>
      ${s.body}
    </section>
  `).join("");
}

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const pw = document.getElementById("pw").value;
  const err = document.getElementById("loginError");
  err.textContent = "";
  try {
    const content = await decrypt(pw);
    document.getElementById("login").style.display = "none";
    document.getElementById("app").classList.add("active");
    render(content);
    sessionStorage.setItem("sb_pw", pw);
  } catch (e) {
    err.textContent = "Wrong password";
  }
});

(async () => {
  const stored = sessionStorage.getItem("sb_pw");
  if (stored) {
    try {
      const content = await decrypt(stored);
      document.getElementById("login").style.display = "none";
      document.getElementById("app").classList.add("active");
      render(content);
    } catch (e) {
      sessionStorage.removeItem("sb_pw");
    }
  }
})();
</script>

</body>
</html>
"""

html = HTML.replace("__BLOB__", json.dumps(blob))
out = os.path.expanduser("~/Documents/Claude/sparkbank-guide/index.html")
with open(out, "w") as f:
    f.write(html)
print(f"wrote {out} ({len(html)} bytes)")
print(f"password: {PASSWORD}")
