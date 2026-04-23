fn fat(n:i32) -> i32 {
  if (n < 2) {
    return 1;
  }
  return n * fat(n - 1);
}

fn fib(n:i32) -> i32 {
  if (n < 2) {
    return n;
  }
  return fib(n - 1) + fib(n - 2);
}

fn greet(name:str) -> () {
  println!(name);
}

fn main() -> () {
  let mut i:i32;
  println!(fat(5));
  println!(fat(6));
  println!(fib(10));
  greet("hello");
  i = 0;
  while (i < 3) {
    println!(fat(i + 1));
    i = i + 1;
  }
}
