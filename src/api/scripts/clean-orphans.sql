DELETE
FROM _Station
WHERE id IN (
    SELECT
      _Station.id
    FROM
      _Station
      LEFT JOIN _PointDeCharge ON station_id = _Station.id
    WHERE
      _PointDeCharge.station_id ISNULL
);

DELETE
FROM Amenageur
WHERE id IN (
    SELECT
      Amenageur.id
    FROM
      Amenageur
      LEFT JOIN _Station ON amenageur_id = Amenageur.id
    WHERE
      _Station.amenageur_id ISNULL
);

DELETE
FROM Operateur
WHERE id IN (
    SELECT
      Operateur.id
    FROM
      Operateur
      LEFT JOIN _Station ON operateur_id = Operateur.id
    WHERE
      _Station.operateur_id ISNULL
);

DELETE
FROM Localisation
WHERE id IN (
    SELECT
      Localisation.id
    FROM
      Localisation
      LEFT JOIN _Station ON localisation_id = Localisation.id
    WHERE
      _Station.localisation_id ISNULL
);
