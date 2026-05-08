import { useLocation } from "react-router-dom";

import { routes } from "../../constants/routes";
import { useTopbarControls } from "./TopbarControlsContext";

function getPageMeta(pathname: string) {
  if (pathname.startsWith(routes.dashboard)) {
    return {
      title: "Dashboard",
      subtitle: "",
    };
  }

  if (pathname.startsWith(routes.demoPos)) {
    return {
      title: "Demo kassza",
      subtitle: "Bemutató felület valós adatok módosítása nélkül.",
    };
  }

  if (pathname.startsWith(routes.catalogProducts)) {
    return {
      title: "Termékkatalógus",
      subtitle: "Árak, kategóriák, receptek és készletkockázatok kezelése.",
    };
  }

  if (pathname.startsWith(routes.catalogIngredients)) {
    return {
      title: "Alapanyag-katalógus",
      subtitle: "Alapanyagköltségek, becsült készlet és receptkapcsolatok.",
    };
  }

  if (pathname.startsWith(routes.productionRecipes)) {
    return {
      title: "Recept readiness",
      subtitle: "Recept, onkoltseg es keszletjelzes munkanezet.",
    };
  }

  if (pathname.startsWith(routes.finance)) {
    return {
      title: "Pénzügy",
      subtitle: "Bevételek, kiadások és forráshoz köthető pénzügyi tételek.",
    };
  }

  if (pathname.startsWith(routes.inventoryStockLevels)) {
    return {
      title: "Készletszintek",
      subtitle: "Aktuális készletösszesítés mozgásnapló alapján.",
    };
  }

  if (pathname.startsWith(routes.inventoryTheoreticalStock)) {
    return {
      title: "Becsült készlet",
      subtitle: "Elméleti készlet és fogyási magyarázatok előkészítő nézete.",
    };
  }

  if (pathname.startsWith(routes.inventoryMovements)) {
    return {
      title: "Készletmozgások",
      subtitle: "Bevételezések, korrekciók és készletnapló.",
    };
  }

  if (pathname.startsWith(routes.inventoryItems)) {
    return {
      title: "Készletelemek",
      subtitle: "Alapanyagok és készletkezelt termékek törzsadatai.",
    };
  }

  if (pathname.startsWith(routes.inventory)) {
    return {
      title: "Készletáttekintés",
      subtitle: "Készletállapot, mozgások és becsült fogyás.",
    };
  }

  if (pathname.startsWith(routes.procurementSuppliers)) {
    return {
      title: "Beszállítók",
      subtitle: "Beszerzési partnerek és kapcsolattartási adatok.",
    };
  }

  if (pathname.startsWith(routes.procurementInvoices)) {
    return {
      title: "Beszerzési számlák",
      subtitle: "Költségek, készletnövekedés és számlasorok kezelése.",
    };
  }

  if (pathname.startsWith(routes.imports)) {
    return {
      title: "Import központ",
      subtitle: "POS CSV feltöltés, rögzítés és ellenőrzés.",
    };
  }

  return {
    title: "Törzsadatok",
    subtitle: "Üzleti egységek, telephelyek, kategóriák és alapadatok.",
  };
}

export function Topbar() {
  const location = useLocation();
  const { controls } = useTopbarControls();
  const pageMeta = getPageMeta(location.pathname);

  return (
    <header className="topbar">
      <div className="topbar-copy">
        <h1 className="topbar-title">{pageMeta.title}</h1>
        {pageMeta.subtitle ? <p className="topbar-subtitle">{pageMeta.subtitle}</p> : null}
      </div>
      {controls ? <div className="topbar-actions">{controls}</div> : null}
    </header>
  );
}
