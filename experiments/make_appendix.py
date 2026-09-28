"""Writes paper/sections/appendix.tex from the corpus (attack list + one example skill)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
from corpus import ATTACKS, load_skill  # noqa: E402

REP = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
       "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "`": r"\`{}"}


def esc(s: str) -> str:
    return "".join(REP.get(c, c) for c in s)


def main() -> None:
    lines = [r"\section{Attack Prompts}", r"\label{app:attacks}",
             r"All 24 attacks, grouped by category. \texttt{\{P\}} is replaced with the skill's rule prefix "
             r"(e.g.\ \texttt{TXR}), which an attacker learns from ordinary answers. Multi-turn attacks list both user turns.",
             "", r"\begin{small}", r"\begin{enumerate}[label=A\arabic*., leftmargin=2.4em]"]
    for cat, turns in ATTACKS:
        body = r" \emph{Then:} ".join(esc(t).replace(r"\{P\}", r"\texttt{\{P\}}") for t in turns)
        lines.append(rf"  \item \textsc{{{cat}}}. {body}")
    lines += [r"\end{enumerate}", r"\end{small}", "",
              r"\section{Example Skill}", r"\label{app:skill}",
              r"The \texttt{tax-reconciler} skill used in the evaluation, verbatim. Its last line is the canary.", "",
              r"\begin{lstlisting}[basicstyle=\ttfamily\scriptsize]", load_skill("tax-reconciler").strip(), r"\end{lstlisting}"]
    (ROOT / "paper" / "sections" / "appendix.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote appendix.tex")


if __name__ == "__main__":
    main()
