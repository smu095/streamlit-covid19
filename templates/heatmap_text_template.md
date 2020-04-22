The infection heatmap actually shows the *normalised* number of new cases by time. Specifically, the number of new cases, denoted $\Delta x$, for each date in a given country has been scaled according to the following formula:

$\Delta x_{scaled} = \dfrac{\Delta x - min(\Delta x)}{max(\Delta x) - min(\Delta x)}$.

Each country is represented by a horisontal strip, where the colour of each field represents the number of new cases for a given date.

If the fields change colour from grey to red, the number of new cases are *increasing*. If the fields change colour from red to grey, the number of new cases are *decreasing*. Dark red fields indicate that the number of new cases is close to the overall maximum of new cases for a given country.