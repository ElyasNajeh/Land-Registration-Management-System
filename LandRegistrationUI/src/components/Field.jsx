import { labelize } from "../utils";

export default function Field({ label, name, type = "text", options, full = false, ...props }) {
  return <div className={`form-field ${full ? "full" : ""}`}><label htmlFor={name}>{label}</label>{options ? <select id={name} name={name} {...props}>{options.map((option) => { const item = typeof option === "string" ? { value: option, label: labelize(option) } : option; return <option key={item.value} value={item.value}>{item.label}</option>; })}</select> : type === "textarea" ? <textarea id={name} name={name} rows="4" {...props} /> : <input id={name} name={name} type={type} {...props} />}</div>;
}
