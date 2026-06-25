# Backup and Push Task Checklist

- [x] Clean up build directories
  - [x] Run `cargo clean` inside `agam` folder
  - [x] Delete `benchmarks/build` directory
  - [x] Delete `agam/dist` directory
  - [x] Delete `agam/.agam_cache` directory
  - [x] Delete `agam/graphify-out` directory
- [ ] Commit and Push parent repository changes
  - [ ] Check git status of parent repo
  - [ ] Commit parent repo changes
  - [ ] Push parent repo changes to GitHub
- [ ] Commit and Push `agam` sub-repository changes
  - [ ] Check git status of `agam` repo
  - [ ] Commit `agam` repo changes
  - [ ] Push `agam` repo changes to GitHub
- [ ] Verify
  - [ ] Measure total workspace size (should be under 500 MB)
  - [ ] Check git status is clean or only has ignored folders
