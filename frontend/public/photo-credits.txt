# Football photography

The displayed photographs are bundled locally and embedded in `index.html`; they do not require a live image service. They show Premier League players, not verified current squad membership. The photographs do not imply endorsement.

| Asset | Author / original source | Licence |
|---|---|---|
| `haaland.jpg` | Jacek Stanislawek — [Erling Haaland, 2023](https://commons.wikimedia.org/wiki/File:Erling_Haaland_2023_(fullcropped-v2).jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| `salah.png` | User-supplied Mohamed Salah photograph, replacing the Saka photo | Photographer and licence unspecified; no open-licence claim is made |

Original image bytes are retained. Presentation uses CSS cropping, colour toning, rotation and overlays. Any adaptation of the Haaland photograph is offered under CC BY-SA 4.0; this includes its rendered/cropped presentation. That licence applies to the photo adaptation, not to the independently licensed app code. Preserve these credits and the in-page attribution when redistributing. No player images were generated with AI. The supplied Salah image is not covered by the app's MIT licence or Haaland's CC licence.

The fluid simulation in the standalone HTML is adapted from Pavel Dobryakov's WebGL Fluid Simulation, MIT, copyright 2017. The complete licence is in `LICENSE-fluid.txt`. The supplied Flowstate reference provided the tuned engine; the football version changes the colours and respects reduced motion. Streamlit uses the shared hero HTML and CSS animation because Streamlit 1.45 sanitizes embedded JavaScript; the standalone preview additionally runs WebGL.

The primary React app now uses the same WebGL scene as a lifecycle-managed module, with native pause/reduced-motion controls and a smaller simulation grid on phones. The image files are copied unchanged into `frontend/public/photos/` and the built frontend. Source and licence credits remain visible in the hero and at `/photo-credits.txt`; `frontend/public/LICENSE-fluid.txt` preserves the animation licence in the deployed app.
