export default function BrandLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { id: string };
}) {
  return (
    <div className="min-h-screen" data-brand-id={params.id}>
      {children}
    </div>
  );
}
