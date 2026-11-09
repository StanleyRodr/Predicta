import { useQuery } from "@tanstack/react-query";
import { getProducts } from "../../api/analytics";
import { useAuthStore } from "../../stores/authStore";

export interface CategoryProduct {
  categoria: string;
  producto: string;
}

interface CategoryProductFilterProps {
  categories: string[];
  value: CategoryProduct;
  onChange: (value: CategoryProduct) => void;
  categoryLabel?: string;
  allCategoriesLabel?: string;
}

const selectClass =
  "rounded-md border border-terminal-border bg-terminal-bg px-2 py-1.5 text-terminal-text disabled:cursor-not-allowed disabled:opacity-50";

/** Category select plus a product select that lists only that category's products. */
export function CategoryProductFilter({
  categories,
  value,
  onChange,
  categoryLabel = "Categoría",
  allCategoriesLabel = "Todas las categorías",
}: CategoryProductFilterProps) {
  const userId = useAuthStore((state) => state.user?.id_usuario ?? null);
  const products = useQuery({
    queryKey: ["analytics", userId, "products", value.categoria],
    queryFn: () => getProducts(value.categoria),
    enabled: userId !== null && value.categoria !== "",
  });
  const names = value.categoria ? (products.data?.productos ?? []) : [];

  return (
    <>
      <label className="flex items-center gap-2 text-sm text-terminal-muted">
        {categoryLabel}
        <select
          className={selectClass}
          onChange={(event) => onChange({ categoria: event.target.value, producto: "" })}
          value={value.categoria}
        >
          <option value="">{allCategoriesLabel}</option>
          {categories.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </label>
      <label className="flex items-center gap-2 text-sm text-terminal-muted">
        Producto
        <select
          className={selectClass}
          disabled={!value.categoria}
          onChange={(event) => onChange({ categoria: value.categoria, producto: event.target.value })}
          title={value.categoria ? undefined : "Elige primero una categoría"}
          value={value.producto}
        >
          <option value="">Todos los productos</option>
          {names.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </label>
    </>
  );
}
