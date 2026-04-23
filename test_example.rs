let mut b:i32 = 5;

fn soma(x:i32, y:i32) -> i32 {
  let mut a:i32;
  a = x + y;
  println!(a);
  return a;
}

fn main() -> () {
  let mut a:i32;
  {
    let mut b:i32;
    a = 3;
    b = soma(a, 4);
    println!(b);
  }
  println!(a);
  println!(b);
}
