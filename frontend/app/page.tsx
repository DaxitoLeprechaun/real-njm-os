import BrandCard from "@/components/njm/BrandCard";

interface Brand {
  id: string;
  nombre: string;
  sector: string;
  saludAdn: number;
}

const MOCK_BRANDS: Brand[] = [
  { id: "disrupt",  nombre: "Disrupt",       sector: "Consultoría SaaS",    saludAdn: 85 },
  { id: "acme",     nombre: "Acme Corp",      sector: "E-commerce",          saludAdn: 30 },
  { id: "nova",     nombre: "Nova Studio",    sector: "Diseño & Branding",   saludAdn: 62 },
  { id: "zenpay",   nombre: "ZenPay",         sector: "Fintech",             saludAdn: 91 },
  { id: "leafco",   nombre: "LeafCo",         sector: "Agritech",            saludAdn: 48 },
  { id: "synthos",  nombre: "Synthos AI",     sector: "IA Aplicada",         saludAdn: 74 },
];

export default function AgencyHubPage() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Agency Hub</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Portfolio de marcas — {MOCK_BRANDS.length} activas
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {MOCK_BRANDS.map((brand) => (
          <BrandCard key={brand.id} {...brand} />
        ))}
      </div>
    </div>
  );
}
