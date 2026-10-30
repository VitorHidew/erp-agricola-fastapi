from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from typing import List

from sqlmodel import Session, select

from .models import (
    ChartAccount,
    CostCenter,
    FinancialEntry,
    FinancialEntryType,
    FinancialStatus,
    InventoryCount,
    OrderLineIn,
    OrderStatus,
    OrderType,
    Party,
    PartyKind,
    Product,
    ProductCategory,
    SalesOrder,
    SalesOrderLine,
    StockMovement,
    StockMovementType,
    WarehouseLocation,
)


def _rng() -> random.Random:
    return random.Random(42)


def seed_reference(session: Session) -> None:
    if not session.exec(select(ChartAccount).limit(1)).first():
        accounts = [
            ChartAccount(code="3.1.01", name="Vendas de produtos", nature="Receita"),
            ChartAccount(code="3.1.02", name="Serviços", nature="Receita"),
            ChartAccount(code="4.1.01", name="Matéria-prima", nature="Despesa"),
            ChartAccount(code="4.1.02", name="Frete e logística", nature="Despesa"),
            ChartAccount(code="4.1.03", name="Pessoal", nature="Despesa"),
            ChartAccount(code="4.1.04", name="Utilidades", nature="Despesa"),
            ChartAccount(code="1.1.02", name="Contas a receber", nature="Ativo"),
            ChartAccount(code="2.1.01", name="Fornecedores", nature="Passivo"),
        ]
        for a in accounts:
            session.add(a)
        session.flush()

    if not session.exec(select(CostCenter).limit(1)).first():
        centers = [
            CostCenter(code="CC-PROD", name="Produção rural"),
            CostCenter(code="CC-ADM", name="Administrativo"),
            CostCenter(code="CC-COM", name="Comercial"),
        ]
        for c in centers:
            session.add(c)
        session.flush()

    if not session.exec(select(WarehouseLocation).limit(1)).first():
        locs = [
            WarehouseLocation(code="CAMARA-1", name="Câmara fria"),
            WarehouseLocation(code="GALPAO-1", name="Galpão principal"),
            WarehouseLocation(code="FEIRA", name="Banca da feira"),
            WarehouseLocation(code="COLHEITA", name="Área de colheita"),
        ]
        for w in locs:
            session.add(w)


def seed_parties_volume(session: Session) -> None:
    clients = [
        (f"Cliente Exemplo {i:02d}", f"CLIENTE-{i:02d}")
        for i in range(1, 11)
    ]
    suppliers = [
        (f"Fornecedor Exemplo {i:02d}", f"FORNECEDOR-{i:02d}")
        for i in range(1, 8)
    ]
    extras = _rng().sample(range(1000, 9999), 25)
    n = 0
    for name, doc in clients:
        p = Party(name=name, kind=PartyKind.cliente, document=doc, phone=f"(00) 00000-{n:04d}")
        session.add(p)
        n += 1
    for name, doc in suppliers:
        p = Party(name=name, kind=PartyKind.fornecedor, document=doc, phone=f"(00) 00000-{n:04d}")
        session.add(p)
        n += 1
    for i in range(12):
        pname = f"Cliente Genérico {i+1:02d}"
        p = Party(name=pname, kind=PartyKind.cliente, document=None, phone=None)
        session.add(p)
    session.flush()


def _categories() -> List[ProductCategory]:
    return list(ProductCategory)


def seed_products_volume(session: Session) -> List[Product]:
    rng = _rng()
    cats = _categories()
    skus: List[Product] = []
    catalog = [
        ("Alface crespa", ProductCategory.hortalicas, "unidade", 3.5),
        ("Couve", ProductCategory.hortalicas, "maço", 4.0),
        ("Rúcula", ProductCategory.hortalicas, "maço", 4.5),
        ("Tomate", ProductCategory.legumes, "kg", 8.0),
        ("Cenoura", ProductCategory.legumes, "kg", 6.0),
        ("Abobrinha", ProductCategory.legumes, "kg", 5.5),
        ("Banana-prata", ProductCategory.frutas, "kg", 7.0),
        ("Laranja", ProductCategory.frutas, "kg", 5.0),
        ("Mamão", ProductCategory.frutas, "unidade", 8.5),
        ("Feijão", ProductCategory.graos, "kg", 12.0),
        ("Milho verde", ProductCategory.graos, "bandeja", 7.5),
        ("Ovos caipiras", ProductCategory.ovos_laticinios, "dúzia", 14.0),
        ("Queijo fresco", ProductCategory.ovos_laticinios, "unidade", 24.0),
        ("Geleia artesanal", ProductCategory.processados, "pote", 18.0),
        ("Mel", ProductCategory.processados, "frasco", 28.0),
    ]
    for i in range(85):
        base_name, cat, unit, base_price = catalog[i % len(catalog)]
        sku = f"AGR-{1000+i}"
        name = f"{base_name} - lote {i+1:02d}"
        sell = base_price * rng.uniform(0.9, 1.2)
        cost = sell * rng.uniform(0.5, 0.75)
        qty = round(rng.uniform(8, 80), 2)
        min_s = round(qty * rng.uniform(0.12, 0.28), 2)
        harvest = date.today() - timedelta(days=rng.randint(0, 5))
        shelf_life = 5 if cat in (ProductCategory.hortalicas, ProductCategory.frutas) else 20
        p = Product(
            sku=sku,
            name=name,
            category=cat,
            unit=unit,
            harvest_date=harvest,
            expiry_date=harvest + timedelta(days=shelf_life + rng.randint(0, 7)),
            public_sale=True,
            density_kg_m3=None,
            qty_m3=qty,
            cost_per_m3=cost,
            avg_cost_per_m3=cost,
            sell_price_per_m3=round(sell, 2),
            min_stock_m3=min_s,
            supplier_name=rng.choice(["Fornecedor Exemplo 01", "Fornecedor Exemplo 02", "Fornecedor Exemplo 03"]),
        )
        session.add(p)
        skus.append(p)
    session.flush()
    return skus


def seed_movements_volume(session: Session, products: List[Product]) -> None:
    rng = _rng()
    parties = session.exec(select(Party)).all()
    locs = session.exec(select(WarehouseLocation)).all()
    loc_codes = [l.code for l in locs] or [None]
    skus = [p.sku for p in products]
    party_names = [p.name for p in parties] if parties else ["Cliente X"]
    base = date.today() - timedelta(days=120)
    for i in range(220):
        dt = base + timedelta(days=rng.randint(0, 120))
        sku = rng.choice(skus)
        is_in = rng.random() < 0.45
        if is_in:
            mtype = StockMovementType.entrada
            vol = round(rng.uniform(3, 18), 2)
            unit = round(rng.uniform(2, 20), 2)
        else:
            if rng.random() < 0.08:
                mtype = StockMovementType.ajuste
                vol = round(rng.uniform(-2, 2), 2)
                unit = None
            else:
                mtype = StockMovementType.saida
                vol = round(rng.uniform(1, 10), 2)
                unit = round(rng.uniform(3, 30), 2)
        total = None if unit is None else round(unit * abs(vol), 2)
        batch = f"LT-{dt.year}{dt.month:02d}-{rng.randint(1, 900):03d}" if mtype == StockMovementType.entrada else None
        confirmed = None
        if mtype == StockMovementType.entrada and rng.random() < 0.75:
            confirmed = datetime.utcnow()
        session.add(
            StockMovement(
                movement_date=dt,
                movement_type=mtype,
                document_no=f"#{'ENT' if is_in else 'SAI'}-{4200+i}",
                product_sku=sku,
                volume_m3=vol,
                unit_value=unit,
                total_value=total,
                party_name=rng.choice(party_names),
                nf_no=f"NF {8000+i}" if rng.random() > 0.12 else None,
                warehouse_location_code=rng.choice(loc_codes),
                batch_lot=batch,
                confirmed_at=confirmed,
            )
        )


def seed_finance_volume(session: Session) -> None:
    rng = _rng()
    parties = session.exec(select(Party)).all()
    names = [p.name for p in parties] if parties else ["Cliente"]
    accounts = session.exec(select(ChartAccount)).all()
    acc_ids = [a.id for a in accounts] or [None]
    centers = session.exec(select(CostCenter)).all()
    cc_ids = [c.id for c in centers] or [None]
    base = date.today() - timedelta(days=180)
    for i in range(160):
        is_pagar = rng.random() < 0.48
        et = FinancialEntryType.pagar if is_pagar else FinancialEntryType.receber
        dt = base + timedelta(days=rng.randint(0, 200))
        amt = round(rng.uniform(50, 3500), 2)
        st = rng.choices(
            [FinancialStatus.aberto, FinancialStatus.pago, FinancialStatus.vencido],
            weights=[0.42, 0.38, 0.20],
            k=1,
        )[0]
        paid = datetime.utcnow() - timedelta(days=rng.randint(1, 40)) if st == FinancialStatus.pago else None
        session.add(
            FinancialEntry(
                entry_type=et,
                due_date=dt,
            description=f"Movimento da produção #{3200+i}",
                party_name=rng.choice(names),
                category=rng.choice(["Insumos", "Vendas", "Produção", "Transporte", "Feira"]),
                amount=amt,
                status=st,
                paid_at=paid,
                notes=None,
                chart_account_id=rng.choice(acc_ids),
                cost_center_id=rng.choice(cc_ids),
                reconciled=st == FinancialStatus.pago and rng.random() < 0.35,
                reconcile_ref=f"EXTRATO-{rng.randint(100,999)}" if rng.random() < 0.3 else None,
            )
        )


def _compute_order_total(lines: List[OrderLineIn], discount_order_pct: float) -> float:
    sub = 0.0
    for ln in lines:
        disc = max(0.0, min(100.0, ln.discount_line_pct))
        sub += ln.volume_m3 * ln.unit_price * (1 - disc / 100.0)
    d = max(0.0, min(100.0, discount_order_pct))
    return round(sub * (1 - d / 100.0), 2)


def seed_orders_volume(session: Session, products: List[Product]) -> None:
    rng = _rng()
    clients = [p for p in session.exec(select(Party)).all() if p.kind == PartyKind.cliente]
    suppliers = [p for p in session.exec(select(Party)).all() if p.kind == PartyKind.fornecedor]
    skus = [p.sku for p in products]
    if not skus:
        return
    year = date.today().year
    for i in range(72):
        is_venda = rng.random() < 0.62
        otype = OrderType.venda if is_venda else OrderType.compra
        party_list = clients if is_venda else suppliers
        party = rng.choice(party_list) if party_list else None
        pname = party.name if party else ("Cliente Avulso" if is_venda else "Fornecedor Avulso")
        pid = party.id if party else None
        nlines = rng.randint(1, 4)
        lines_in: List[OrderLineIn] = []
        for _ in range(nlines):
            sku = rng.choice(skus)
            vol = round(rng.uniform(1, 12), 2)
            unit = round(rng.uniform(3, 30), 2)
            ld = round(rng.uniform(0, 8), 2) if rng.random() < 0.15 else 0.0
            lines_in.append(OrderLineIn(product_sku=sku, volume_m3=vol, unit_price=unit, discount_line_pct=ld))
        disc_order = round(rng.uniform(0, 5), 2) if rng.random() < 0.12 else 0.0
        total = _compute_order_total(lines_in, disc_order)
        first = lines_in[0]
        status = rng.choices(
            [OrderStatus.rascunho, OrderStatus.aprovado, OrderStatus.faturado, OrderStatus.cancelado],
            weights=[0.22, 0.28, 0.42, 0.08],
            k=1,
        )[0]
        delivery = date.today() + timedelta(days=rng.randint(-5, 25)) if rng.random() > 0.25 else None
        order = SalesOrder(
            order_code=f"PED-{year}-{4200+i:04d}",
            order_date=date.today() - timedelta(days=rng.randint(0, 90)),
            order_type=otype,
            status=status,
            party_name=pname,
            party_id=pid,
            product_sku=first.product_sku,
            volume_m3=first.volume_m3,
            unit_price=first.unit_price,
            total_value=total,
            delivery_date=delivery,
            discount_order_pct=disc_order,
            notes=f"Pedido demonstrativo #{i}" if rng.random() > 0.4 else None,
        )
        session.add(order)
        session.flush()
        for ln in lines_in:
            session.add(
                SalesOrderLine(
                    order_id=order.id,
                    product_sku=ln.product_sku,
                    volume_m3=ln.volume_m3,
                    unit_price=ln.unit_price,
                    discount_line_pct=ln.discount_line_pct,
                )
            )


def seed_inventory_sample(session: Session, products: List[Product]) -> None:
    rng = _rng()
    if session.exec(select(InventoryCount).limit(1)).first():
        return
    sample = rng.sample(products, min(25, len(products)))
    for p in sample:
        sys_q = float(p.qty_m3 or 0)
        counted = round(sys_q + rng.uniform(-1.5, 1.5), 2)
        session.add(
            InventoryCount(
                product_sku=p.sku,
                qty_system=sys_q,
                qty_counted=counted,
                variance=round(counted - sys_q, 2),
                notes="Contagem ciclo seed",
            )
        )


def sync_product_stock_from_db(session: Session) -> None:
    """Recalcula a quantidade a partir das movimentações (coerência pós-seed)."""
    products = session.exec(select(Product)).all()
    movements = session.exec(select(StockMovement)).all()
    by_sku: dict[str, float] = {p.sku: 0.0 for p in products}
    for m in movements:
        if m.product_sku not in by_sku:
            continue
        v = float(m.volume_m3)
        if m.movement_type == StockMovementType.saida:
            by_sku[m.product_sku] -= v
        elif m.movement_type == StockMovementType.entrada:
            by_sku[m.product_sku] += v
        else:
            by_sku[m.product_sku] += v
    for p in products:
        p.qty_m3 = round(max(0, by_sku.get(p.sku, 0)), 3)
        session.add(p)


def bulk_seed(session: Session) -> None:
    seed_reference(session)
    seed_parties_volume(session)
    products = seed_products_volume(session)
    seed_movements_volume(session, products)
    sync_product_stock_from_db(session)
    seed_finance_volume(session)
    seed_orders_volume(session, products)
    seed_inventory_sample(session, products)
    session.commit()


