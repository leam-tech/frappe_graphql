## Adding a newly created DocType

- Generate the SDLs in your app directory

  ```bash
  # Generate SDLs for all doctypes in <your-app>
  $ bench --site test_site graphql generate_sdl --output-dir <your-app/graphql> --app <your-app>

  # Generate SDLs for all doctype in module <m1> <m2>
  $ bench --site test_site graphql generate_sdl --output-dir <your-app/graphql> --module <m1> -m <m2> -m <name>

  # Generate SDLs for doctype <d1> <2>
  $ bench --site test_site graphql generate_sdl --output-dir <your-app/graphql> --doctype <d1> -dt <d2> -dt <name>

  # Generate SDLs for all doctypes in <your-app> without Enums for Select Fields
  $ bench --site test_site graphql generate_sdl --output-dir <your-app/graphql> --app <your-app> --disable-enum-select-fields
  ```

- Specify this directory in `graphql_sdl_dir` hook and you are done.
