const STATUS_INFO = {
  FALTANTE: { label: "Faltante", className: "bg-faltante text-white" },
  DISPONIBLE_PARA_PEGAR: { label: "Disponible", className: "bg-disponible text-white" },
  PEGADA_SIN_REPETIDA: { label: "Pegada", className: "bg-pegada text-white" },
  PEGADA_CON_REPETIDA: { label: "Pegada + repetida", className: "bg-repetida text-black" },
};

export default function StatusBadge({ status }) {
  const info = STATUS_INFO[status] || { label: status, className: "bg-gray-300 text-black" };

  return (
    <span className={`inline-block rounded-full px-3 py-1 text-sm font-semibold ${info.className}`}>
      {info.label}
    </span>
  );
}
