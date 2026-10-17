function SafetyNotice({ className = '' }) {
  return (
    <aside className={`safetyNotice ${className}`.trim()} aria-label="Important notice">
      <strong>Please note</strong>
      <ul>
        <li>Verif-AI is AI-generated and can make mistakes. Please double-check important details yourself.</li>
        <li>
          This is general information, not legal or professional advice. Do your own research and consult
          a lawyer or the Public Attorney&apos;s Office for your specific situation.
        </li>
        <li>
          If you feel unsafe or are in danger, contact the relevant authorities right away (e.g. your
          barangay, the police, or emergency services at 911).
        </li>
        <li>Verif-AI is not responsible for decisions or outcomes based on this information.</li>
      </ul>
    </aside>
  );
}

export default SafetyNotice;
