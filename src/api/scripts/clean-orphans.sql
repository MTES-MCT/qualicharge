DELETE
FROM Station
WHERE id IN (
    SELECT
      Station.id
    FROM
      Station
      LEFT JOIN PointDeCharge ON station_id = Station.id
    WHERE
      PointDeCharge.station_id ISNULL
);

DELETE
FROM Amenageur
WHERE id IN (
    SELECT
      Amenageur.id
    FROM
      Amenageur
      LEFT JOIN Station ON amenageur_id = Amenageur.id
    WHERE
      Station.amenageur_id ISNULL
);

DELETE
FROM Operateur
WHERE id IN (
    SELECT
      Operateur.id
    FROM
      Operateur
      LEFT JOIN Station ON operateur_id = Operateur.id
    WHERE
      Station.operateur_id ISNULL
);

DELETE
FROM Localisation
WHERE id IN (
    SELECT
      Localisation.id
    FROM
      Localisation
      LEFT JOIN Station ON localisation_id = Localisation.id
    WHERE
      Station.localisation_id ISNULL
);
